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

addMessage("agent", greeting, {
  tags: [{ label: "workflow", value: "ready" }],
});

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
      intent: normalizedIntent(result),
      policy: policyLabel(result),
      tool: toolLabel(result.workflow),
      outcome: decisionLabel(result),
      hot: result.workflow === "human_handoff" || result.status === "requires_approval",
    });
    addMessage("agent", result.reply, {
      tags: [
        { label: "intent", value: normalizedIntent(result) },
        { label: "workflow", value: normalizedWorkflow(result) },
        { label: "decision", value: decisionLabel(result) },
      ],
      policyReason: policyReason(result),
      trace: decisionTrace(result),
    });
  } catch (error) {
    setDecisionState({
      intent: "Error",
      policy: "Unknown",
      tool: "API",
      outcome: "Failed",
      hot: true,
    });
    addMessage("agent", "I could not reach the workflow API. Please check the backend service.", {
      tags: [{ label: "error", value: error.message }],
    });
  }
});

function addMessage(role, text, options = {}) {
  const tags = options.tags || [];
  const bubble = document.createElement("article");
  bubble.className = `message ${role}`;

  const body = document.createElement("div");
  body.textContent = text;
  bubble.appendChild(body);

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

  if (options.policyReason || options.trace) {
    const evidence = document.createElement("div");
    evidence.className = "evidence-block";

    if (options.policyReason) {
      const reason = document.createElement("section");
      reason.className = "evidence-section";
      reason.innerHTML = `<h4>Policy reason</h4><p>${escapeHtml(options.policyReason)}</p>`;
      evidence.appendChild(reason);
    }

    if (options.trace) {
      const trace = document.createElement("section");
      trace.className = "evidence-section";
      trace.innerHTML = `
        <h4>Decision trace</h4>
        <div class="trace-grid">
          ${options.trace
            .map(
              (item) => `
                <div class="trace-item">
                  <span>${escapeHtml(item.label)}</span>
                  <strong>${escapeHtml(item.value)}</strong>
                </div>
              `
            )
            .join("")}
        </div>
      `;
      evidence.appendChild(trace);
    }

    bubble.appendChild(evidence);
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
  const decision = decisionLabel(result);
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

function normalizedIntent(result) {
  if (result.workflow === "human_handoff") return "escalation";
  return result.intent;
}

function normalizedWorkflow(result) {
  return result.workflow;
}

function decisionLabel(result) {
  if (result.workflow === "human_handoff") return "escalated";
  if (result.data?.policy_decision?.decision === "approved") return "approved";
  if (result.data?.policy_decision?.decision === "eligible") return "eligible";
  if (result.data?.policy_decision?.decision === "denied") return "denied";
  if (result.data?.policy_decision?.decision === "requires_approval") return "manager_review";
  if (result.status === "requires_approval") return "manager_review";
  if (result.status === "denied") return "denied";
  if (result.status === "resolved") return "resolved";
  return result.status;
}

function policyReason(result) {
  const reason = result.data?.policy_decision?.reason;
  if (reason) return rewritePolicyReason(reason, result);
  if (result.workflow === "human_handoff") return "Customer sentiment or case ambiguity requires human review.";
  if (result.workflow === "wismo") return "Order tracking can be answered without a policy exception.";
  if (result.workflow === "exchange_request") return "Exchange requests require inventory and eligibility review.";
  return "The workflow completed using the matched policy and tool result.";
}

function rewritePolicyReason(reason, result) {
  if (result.workflow === "refund_request" && result.data?.policy_decision?.decision === "approved") {
    return "Refund amount is within the automatic refund limit.";
  }
  if (result.workflow === "refund_request" && result.data?.policy_decision?.decision === "requires_approval") {
    return "Refund amount exceeds the automatic approval threshold.";
  }
  return reason;
}

function decisionTrace(result) {
  return [
    { label: "Confidence", value: confidenceLabel(result) },
    { label: "Policy matched", value: matchedPolicy(result.workflow) },
    { label: "Tool selected", value: selectedTool(result.workflow) },
    { label: "Outcome", value: traceOutcome(result) },
  ];
}

function confidenceLabel(result) {
  if (result.workflow === "human_handoff") return "Medium";
  return "High";
}

function matchedPolicy(workflow) {
  const policies = {
    wismo: "Order Status Policy v1",
    refund_request: "Refund Policy v1",
    return_request: "Returns Policy v1",
    exchange_request: "Exchange Policy v1",
    human_handoff: "Escalation Policy v1",
  };
  return policies[workflow] || "Support Policy v1";
}

function selectedTool(workflow) {
  const tools = {
    wismo: "order_status_lookup",
    refund_request: "refund_processor",
    return_request: "order_status_lookup",
    exchange_request: "support_queue",
    human_handoff: "support_queue",
  };
  return tools[workflow] || "support_queue";
}

function traceOutcome(result) {
  const decision = decisionLabel(result);
  const labels = {
    approved: "Approved",
    eligible: "Eligible",
    denied: "Denied",
    manager_review: "Manager review",
    escalated: "Escalated",
    resolved: "Resolved",
  };
  return labels[decision] || decision;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
