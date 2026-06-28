const state = {
  selectedIntent: "",
};

const customerSelect = document.querySelector("#customerId");
const orderSelect = document.querySelector("#orderId");
const messages = document.querySelector("#messages");
const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const intentCard = document.querySelector("#intentCard strong");
const policyCard = document.querySelector("#policyCard strong");
const toolCard = document.querySelector("#toolCard strong");
const outcomeCard = document.querySelector("#outcomeCard strong");
const decisionCards = document.querySelectorAll(".decision-card");

const orderByCustomer = {
  cus_123: "ord_1001",
  cus_456: "ord_1002",
  cus_789: "ord_1003",
};

const greeting =
  "Hi. I can help with tracking, returns, refunds, exchanges, and human handoff. Choose a request type or just type naturally.";

addMessage("agent", greeting, [{ label: "workflow", value: "ready" }]);

customerSelect.addEventListener("change", () => {
  orderSelect.value = orderByCustomer[customerSelect.value];
});

document.querySelectorAll(".intent-button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".intent-button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    state.selectedIntent = button.dataset.intent;
    intentCard.textContent = state.selectedIntent || "Auto-detect";
  });
});

document.querySelectorAll(".quick-actions button").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.message;
    input.focus();
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  addMessage("user", message);
  setDecisionState({
    intent: state.selectedIntent || "Routing...",
    policy: "Checking",
    tool: "Selecting",
    outcome: "Running",
    hot: false,
  });

  const payload = {
    customer_id: customerSelect.value,
    order_id: orderSelect.value,
    message,
    intent: state.selectedIntent || null,
  };

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }

    const result = await response.json();
    setDecisionState({
      intent: result.intent,
      policy: policyLabel(result),
      tool: toolLabel(result.workflow),
      outcome: result.status,
      hot: result.workflow === "human_handoff" || result.status === "requires_approval",
    });
    addMessage("agent", result.reply, [
      { label: "intent", value: result.intent },
      { label: "workflow", value: result.workflow },
      { label: "status", value: result.status },
    ]);
  } catch (error) {
    setDecisionState({
      intent: "Error",
      policy: "Unknown",
      tool: "API",
      outcome: "Failed",
      hot: true,
    });
    addMessage("agent", "I could not reach the workflow API. Please check the backend service.", [
      { label: "error", value: error.message },
    ]);
  }
});

function addMessage(role, text, tags = []) {
  const bubble = document.createElement("article");
  bubble.className = `message ${role}`;
  bubble.textContent = text;

  if (tags.length > 0) {
    const meta = document.createElement("div");
    meta.className = "meta";
    tags.forEach(({ label, value }) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = `${label}: ${value}`;
      meta.appendChild(tag);
    });
    bubble.appendChild(meta);
  }

  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function setDecisionState({ intent, policy, tool, outcome, hot }) {
  intentCard.textContent = intent;
  policyCard.textContent = policy;
  toolCard.textContent = tool;
  outcomeCard.textContent = outcome;

  decisionCards.forEach((card) => {
    card.classList.add("active");
    card.classList.toggle("hot", hot);
  });
}

function policyLabel(result) {
  const decision = result.data?.policy_decision?.decision;
  if (decision) return decision;
  if (result.workflow === "human_handoff") return "handoff";
  if (result.workflow === "wismo") return "not required";
  return "review";
}

function toolLabel(workflow) {
  const toolsByWorkflow = {
    wismo: "Shopify + Shipping",
    refund_request: "Shopify + Stripe",
    return_request: "Shopify",
    exchange_request: "Shopify + CRM",
    human_handoff: "CRM",
  };
  return toolsByWorkflow[workflow] || "CRM";
}
