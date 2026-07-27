const form = document.querySelector("#reading-form");
const questionInput = document.querySelector("#question");
const cardsInput = document.querySelector("#cards");
const submitButton = document.querySelector("#submit-button");
const exitButton = document.querySelector("#exit-button");
const newReadingButton = document.querySelector("#new-reading");
const followupButton = document.querySelector("#followup");
const chatLog = document.querySelector("#chat-log");
const statusText = document.querySelector("#status-text");
const drawSourceButton = document.querySelector("#draw-source");
const manualSourceButton = document.querySelector("#manual-source");
const drawPanel = document.querySelector("#draw-panel");
const drawButton = document.querySelector("#draw-button");
const drawnCardsEl = document.querySelector("#drawn-cards");
const cardsSummaryEl = document.querySelector("#cards-summary");

const SESSION_ID = "default";
const DRAW_HINT = '<p class="draw-hint">可连续抽取，抽几张就解读几张</p>';

let followupMode = false;
let closed = false;
let cardSource = "draw";
let currentDrawn = [];

const MAJOR_ARCANA = [
  ["The Fool", "愚者"],
  ["The Magician", "魔术师"],
  ["The High Priestess", "女祭司"],
  ["The Empress", "女皇"],
  ["The Emperor", "皇帝"],
  ["The Hierophant", "教皇"],
  ["The Lovers", "恋人"],
  ["The Chariot", "战车"],
  ["Strength", "力量"],
  ["The Hermit", "隐士"],
  ["Wheel of Fortune", "命运之轮"],
  ["Justice", "正义"],
  ["The Hanged Man", "倒吊人"],
  ["Death", "死神"],
  ["Temperance", "节制"],
  ["The Devil", "恶魔"],
  ["The Tower", "高塔"],
  ["The Star", "星星"],
  ["The Moon", "月亮"],
  ["The Sun", "太阳"],
  ["Judgement", "审判"],
  ["The World", "世界"],
];

const SUITS = [
  ["Wands", "权杖"],
  ["Cups", "圣杯"],
  ["Swords", "宝剑"],
  ["Pentacles", "星币"],
];

const RANKS = [
  ["Ace", "一"],
  ["Two", "二"],
  ["Three", "三"],
  ["Four", "四"],
  ["Five", "五"],
  ["Six", "六"],
  ["Seven", "七"],
  ["Eight", "八"],
  ["Nine", "九"],
  ["Ten", "十"],
  ["Page", "侍从"],
  ["Knight", "骑士"],
  ["Queen", "皇后"],
  ["King", "国王"],
];

function buildDeck() {
  const deck = MAJOR_ARCANA.map(([en, cn]) => ({ en, cn }));
  for (const [suitEn, suitCn] of SUITS) {
    for (const [rankEn, rankCn] of RANKS) {
      deck.push({ en: `${rankEn} of ${suitEn}`, cn: `${suitCn}${rankCn}` });
    }
  }
  return deck;
}

const TAROT_DECK = buildDeck();
const CARD_CN_LOOKUP = new Map(
  TAROT_DECK.map((card) => [card.en.toLowerCase(), card.cn]),
);
const CARD_EN_LOOKUP = new Map(TAROT_DECK.map((card) => [card.cn, card.en]));

function createCardElement(card, revealDelay) {
  const wrap = document.createElement("div");
  wrap.className = `tarot-card${card.reversed ? " reversed" : ""}`;
  wrap.innerHTML = `
    <div class="tarot-card-inner">
      <div class="tarot-card-face tarot-card-back"></div>
      <div class="tarot-card-face tarot-card-front">
        <span>${card.cn}<span class="orientation">${card.reversed ? "逆位" : "正位"}</span></span>
      </div>
    </div>
  `;
  window.setTimeout(() => wrap.classList.add("revealed"), revealDelay);
  return wrap;
}

function parseCard(part) {
  const text = String(part).trim();
  const reversedMatch = /\s*(?:\((?:reversed|逆位)\)|reversed|逆位)\s*$/i.exec(text);
  const uprightMatch = /\s*(?:\((?:upright|正位)\)|upright|正位)\s*$/i.exec(text);
  const marker = reversedMatch || uprightMatch;
  const base = marker ? text.slice(0, marker.index).trim() : text;
  const en = CARD_EN_LOOKUP.get(base) || base;
  const cn = CARD_CN_LOOKUP.get(en.toLowerCase()) || base;
  return { en, cn, reversed: Boolean(reversedMatch) };
}

function parseCardsInput(input) {
  if (!input) {
    return [];
  }
  const parts = Array.isArray(input)
    ? input
    : String(input).split(/[,，;；\n]/);
  return parts.map(parseCard).filter((card) => card.en);
}

function cardsForRequest() {
  return parseCardsInput(cardsInput.value)
    .map((card) => `${card.en}${card.reversed ? " reversed" : ""}`)
    .join(", ");
}

function appendDrawnCard(card, index) {
  drawnCardsEl.querySelector(".draw-hint")?.remove();
  drawnCardsEl.appendChild(createCardElement(card, 60 + index * 40));
}

function renderTurnCards(container, cardsData) {
  const cards = parseCardsInput(cardsData);
  if (!cards.length) {
    return false;
  }
  cards.forEach((card, index) => {
    const cardEl = createCardElement(card, 60 + index * 90);
    cardEl.classList.add("tarot-card-sm");
    container.appendChild(cardEl);
  });
  return true;
}

function updateCardsSummary(drawn) {
  cardsSummaryEl.hidden = drawn.length === 0;
  cardsSummaryEl.textContent = drawn
    .map((card) => `${card.cn}${card.reversed ? "（逆位）" : "（正位）"}`)
    .join(" · ");
}

function drawOneCard() {
  const remaining = TAROT_DECK.filter(
    (deckCard) => !currentDrawn.some((drawn) => drawn.en === deckCard.en),
  );
  if (!remaining.length) {
    cardsSummaryEl.hidden = false;
    cardsSummaryEl.textContent =
      "78 张牌已全部抽出，请点击“新解读”开始新的牌组。";
    return;
  }
  const card = {
    ...remaining[Math.floor(Math.random() * remaining.length)],
    reversed: Math.random() < 0.3,
  };
  currentDrawn.push(card);
  appendDrawnCard(card, currentDrawn.length - 1);
  updateCardsSummary(currentDrawn);
  cardsInput.value = currentDrawn
    .map((item) => `${item.en}${item.reversed ? " reversed" : ""}`)
    .join(", ");
}

function resetDraw() {
  currentDrawn = [];
  drawnCardsEl.innerHTML = DRAW_HINT;
  cardsSummaryEl.hidden = true;
  cardsSummaryEl.textContent = "";
  if (cardSource === "draw") {
    cardsInput.value = "";
  }
}

function setCardSource(nextSource) {
  if (nextSource === "manual" && cardSource === "draw") {
    resetDraw();
  }
  cardSource = nextSource;
  const isDraw = cardSource === "draw";
  drawSourceButton.classList.toggle("active", isDraw);
  manualSourceButton.classList.toggle("active", !isDraw);
  drawPanel.classList.toggle("hidden", !isDraw);
  cardsInput.classList.toggle("hidden", isDraw);
  drawSourceButton.setAttribute("aria-pressed", String(isDraw));
  manualSourceButton.setAttribute("aria-pressed", String(!isDraw));
}

function setMode(nextFollowupMode) {
  followupMode = nextFollowupMode;
  newReadingButton.classList.toggle("active", !followupMode);
  followupButton.classList.toggle("active", followupMode);
  newReadingButton.setAttribute("aria-pressed", String(!followupMode));
  followupButton.setAttribute("aria-pressed", String(followupMode));
  cardsInput.placeholder = followupMode
    ? "追问时可以留空；如果补抽了牌，也可以在这里输入"
    : "例如：月亮、女皇逆位、命运之轮（也支持英文牌名）";
  statusText.textContent = followupMode ? "追问模式" : "等待你的问题";
}

function renderEmptyState(
  message = "写下问题并抽取或输入牌面。首次解读需要牌面，之后可直接继续追问。",
) {
  chatLog.innerHTML = `
    <article class="empty-state">
      <h3>开始一次塔罗解读</h3>
      <p></p>
    </article>
  `;
  chatLog.querySelector("p").textContent = message;
}

function ensureChatStarted() {
  chatLog.querySelector(".empty-state")?.remove();
}

function scrollToLatest() {
  window.requestAnimationFrame(() => {
    chatLog.scrollTop = chatLog.scrollHeight;
  });
}

function appendTurn(question, answer, meta, cardsData) {
  ensureChatStarted();
  const turn = document.createElement("article");
  turn.className = "turn";
  turn.innerHTML = `
    <div class="bubble question"></div>
    <div class="turn-cards"></div>
    <div class="bubble answer"></div>
    <div class="meta"></div>
  `;
  turn.querySelector(".question").textContent = question;
  const turnCardsEl = turn.querySelector(".turn-cards");
  if (!renderTurnCards(turnCardsEl, cardsData)) {
    turnCardsEl.remove();
  }
  turn.querySelector(".answer").textContent = answer || "没有返回解读结果。";
  turn.querySelector(".meta").textContent = meta;
  chatLog.appendChild(turn);
  scrollToLatest();
}

function appendNotice(message) {
  ensureChatStarted();
  const notice = document.createElement("div");
  notice.className = "notice";
  notice.textContent = message;
  chatLog.appendChild(notice);
  scrollToLatest();
}

function appendLoadingIndicator() {
  ensureChatStarted();
  const loading = document.createElement("div");
  loading.className = "turn loading-turn";
  loading.id = "loading-indicator";
  loading.innerHTML = `
    <div class="loading-bubble">
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
      <span class="loading-text">正在解读牌面…</span>
    </div>
  `;
  chatLog.appendChild(loading);
  scrollToLatest();
}

function removeLoadingIndicator() {
  document.querySelector("#loading-indicator")?.remove();
}

function setBusy(isBusy) {
  submitButton.disabled = isBusy || closed;
  exitButton.disabled = isBusy || closed;
  submitButton.textContent = isBusy ? "解读中…" : "发送";
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "请求失败，请稍后重试。");
  }
  return data;
}

function setControlsDisabled(disabled) {
  questionInput.disabled = disabled;
  cardsInput.disabled = disabled;
  submitButton.disabled = disabled;
  drawButton.disabled = disabled;
  drawSourceButton.disabled = disabled;
  manualSourceButton.disabled = disabled;
  followupButton.disabled = disabled;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (closed) {
    appendNotice("当前会话已经结束。点击“新解读”可重新开始。");
    return;
  }

  const question = questionInput.value.trim();
  const cards = cardsForRequest();
  if (!question) {
    questionInput.focus();
    return;
  }
  if (!followupMode && !cards) {
    appendNotice("第一次解读请先抽取或输入至少一张牌。");
    if (cardSource === "draw") {
      drawButton.focus();
    } else {
      cardsInput.focus();
    }
    return;
  }

  setBusy(true);
  statusText.textContent = "正在解读...";
  appendLoadingIndicator();
  try {
    const data = await postJson("/api/reading", {
      question,
      cards,
      session_id: SESSION_ID,
      followup: followupMode,
      reset_session: !followupMode,
      use_skills: true,
    });
    removeLoadingIndicator();
    const cardText =
      Array.isArray(data.cards) && data.cards.length
        ? `牌面：${parseCardsInput(data.cards)
            .map((card) => `${card.cn}${card.reversed ? "逆位" : "正位"}`)
            .join(" / ")}`
        : "沿用上一轮牌面";
    appendTurn(
      data.question,
      data.answer,
      `${cardText} · ${data.topic || "综合"} · ${data.turn_mode || "解读"}`,
      data.cards,
    );
    questionInput.value = "";
    resetDraw();
    setMode(true);
    statusText.textContent = "可以继续追问";
  } catch (error) {
    removeLoadingIndicator();
    appendNotice(error.message);
    statusText.textContent = "请求未完成";
  } finally {
    setBusy(false);
  }
});

exitButton.addEventListener("click", async () => {
  setBusy(true);
  try {
    await postJson("/api/exit", { session_id: SESSION_ID });
    closed = true;
    renderEmptyState(
      "本次会话已结束，相关记忆已经清空。浏览器将尝试自动关闭此页面。",
    );
    statusText.textContent = "会话已结束";
    questionInput.value = "";
    cardsInput.value = "";
    setControlsDisabled(true);
    window.setTimeout(() => {
      window.close();
      window.setTimeout(() => {
        statusText.textContent = "会话已结束（请手动关闭页面）";
      }, 400);
    }, 700);
  } catch (error) {
    appendNotice(error.message);
    setBusy(false);
  }
});

newReadingButton.addEventListener("click", async () => {
  setBusy(true);
  newReadingButton.disabled = true;
  statusText.textContent = "正在开始新解读";
  try {
    await postJson("/api/exit", { session_id: SESSION_ID });
    window.location.reload();
  } catch (error) {
    appendNotice(error.message);
    statusText.textContent = "新解读未能开始";
    newReadingButton.disabled = false;
    setBusy(false);
  }
});

followupButton.addEventListener("click", () => setMode(true));
drawButton.addEventListener("click", drawOneCard);
drawSourceButton.addEventListener("click", () => setCardSource("draw"));
manualSourceButton.addEventListener("click", () => setCardSource("manual"));

setCardSource("draw");
setMode(false);

const INTRO_STORAGE_KEY = "agentic-tarot-cn-intro-seen";
const introOverlay = document.querySelector("#intro-overlay");
const helpButton = document.querySelector("#help-button");

function openIntro() {
  introOverlay.classList.remove("hidden");
}

function closeIntro() {
  introOverlay.classList.add("hidden");
  try {
    window.localStorage.setItem(INTRO_STORAGE_KEY, "1");
  } catch {
    // 浏览器禁用本地存储时，不影响页面功能。
  }
}

introOverlay.querySelectorAll("[data-close-intro]").forEach((element) => {
  element.addEventListener("click", closeIntro);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !introOverlay.classList.contains("hidden")) {
    closeIntro();
  }
});

helpButton.addEventListener("click", openIntro);

try {
  if (window.localStorage.getItem(INTRO_STORAGE_KEY) === "1") {
    introOverlay.classList.add("hidden");
  } else {
    openIntro();
  }
} catch {
  openIntro();
}
