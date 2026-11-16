from fastapi.responses import HTMLResponse


UI_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SupportMindAI Support Console</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0b1020;
      --bg-glow: #1d2b54;
      --panel: #121a2d;
      --panel-soft: #17213a;
      --border: #2a3859;
      --text: #eef4ff;
      --muted: #9eacc9;
      --accent: #73a7ff;
      --accent-strong: #4b83ef;
      --success: #48d597;
      --warning: #f3c969;
      --danger: #ff7e8d;
      --shadow: #0003;
    }
    [data-theme="light"] {
      color-scheme: light;
      --bg: #f3f6fb;
      --bg-glow: #dce8ff;
      --panel: #ffffff;
      --panel-soft: #f1f5fb;
      --border: #cbd6e6;
      --text: #17243b;
      --muted: #5d6b82;
      --accent: #2867d8;
      --accent-strong: #1f58bf;
      --success: #147a51;
      --warning: #936700;
      --danger: #b4233c;
      --shadow: #31415b22;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: radial-gradient(circle at top right, var(--bg-glow) 0, var(--bg) 42%);
      color: var(--text);
      font: 15px/1.5 system-ui, -apple-system, Segoe UI, sans-serif;
      transition: background .2s ease, color .2s ease;
    }
    .shell { max-width: 1180px; margin: 0 auto; padding: 28px 20px 52px; }
    header { display: flex; justify-content: space-between; gap: 20px; align-items: end; margin-bottom: 26px; }
    .brand { display: flex; align-items: center; gap: 14px; }
    .brand-mark { display: grid; place-items: center; width: 52px; height: 52px; border-radius: 14px; color: white; background: linear-gradient(135deg, var(--accent-strong), #7b61ff); font-size: 20px; font-weight: 800; letter-spacing: 1px; }
    .brand-name { color: var(--accent); font-size: 13px; font-weight: 800; letter-spacing: 2px; }
    h1, h2, p { margin-top: 0; }
    h1 { margin-bottom: 6px; font-size: clamp(28px, 5vw, 46px); letter-spacing: -1px; }
    h2 { font-size: 19px; margin-bottom: 16px; }
    .subtitle, .hint { color: var(--muted); }
    .header-actions { display: flex; align-items: center; gap: 10px; }
    .badge { color: var(--success); border: 1px solid var(--success); border-radius: 999px; padding: 7px 12px; white-space: nowrap; }
    .theme-toggle { background: var(--panel); color: var(--text); border: 1px solid var(--border); padding: 8px 12px; }
    .grid { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(320px, .85fr); gap: 18px; }
    .card { background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 22px; box-shadow: 0 16px 40px var(--shadow); }
    .wide { grid-column: 1 / -1; }
    label { display: block; color: var(--muted); font-size: 13px; margin: 13px 0 6px; }
    input, textarea, select {
      width: 100%; color: var(--text); background: var(--panel-soft);
      border: 1px solid var(--border); border-radius: 10px; padding: 11px 12px;
      font: inherit; outline: none;
    }
    textarea { min-height: 132px; resize: vertical; }
    input:focus, textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px #73a7ff22; }
    .row { display: flex; gap: 10px; align-items: end; }
    .row > * { flex: 1; }
    button, .link-button {
      border: 0; border-radius: 10px; padding: 11px 15px; color: white;
      background: var(--accent-strong); font-weight: 700; cursor: pointer;
      text-decoration: none; display: inline-block;
    }
    button:hover, .link-button:hover { background: var(--accent); }
    button.secondary { background: #536581; }
    button.danger { background: #a9364d; }
    button:disabled { opacity: .55; cursor: wait; }
    .actions { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 16px; }
    .result { min-height: 150px; margin-top: 14px; padding: 14px; background: var(--panel-soft); border: 1px solid var(--border); border-radius: 12px; overflow-wrap: anywhere; }
    .status { display: inline-block; border-radius: 999px; padding: 3px 9px; background: var(--border); }
    .status.awaiting_approval { color: var(--warning); }
    .status.resolved { color: var(--success); }
    .status.rejected, .status.customer_not_found { color: var(--danger); }
    .metric { display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding: 10px 0; }
    .metric:last-child { border-bottom: 0; }
    .profile { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 14px 0; }
    .profile div { background: var(--panel-soft); border-radius: 10px; padding: 12px; }
    .profile strong, .profile span { display: block; }
    .profile span { color: var(--muted); font-size: 12px; margin-bottom: 3px; }
    .table-wrap { overflow-x: auto; }
    table { border-collapse: collapse; width: 100%; margin-top: 12px; }
    th, td { border-bottom: 1px solid var(--border); padding: 9px 8px; text-align: left; white-space: nowrap; }
    th { color: var(--muted); font-size: 12px; font-weight: 600; }
    .empty { color: var(--muted); padding: 12px 0; }
    .case-card { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .case-field { background: var(--panel-soft); border-radius: 10px; padding: 12px; }
    .case-field.wide { grid-column: 1 / -1; }
    .case-field span { display: block; color: var(--muted); font-size: 12px; margin-bottom: 4px; }
    .case-field strong { display: block; overflow-wrap: anywhere; line-height: 1.4; }
    .case-field .success { color: var(--success); }
    .case-field .warning { color: var(--warning); }
    .case-field .danger { color: var(--danger); }
    footer { margin-top: 22px; color: var(--muted); font-size: 13px; }
    @media (max-width: 780px) {
      header, .grid { display: block; }
      .card { margin-bottom: 18px; }
      .header-actions { align-items: flex-start; margin-top: 16px; }
      .case-card, .profile { grid-template-columns: 1fr; }
      .case-field.wide { grid-column: auto; }
      .row { display: grid; grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div class="brand">
        <div class="brand-mark">S</div>
        <div>
        <div class="brand-name">SUPPORTMINDAI · AGENTIC SUPPORT</div>
        <h1>Support console</h1>
        <p class="subtitle">Investigate customer issues, review recommendations, and approve safe actions.</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()">☀ Light</button>
        <div class="badge">● API online</div>
      </div>
    </header>
    <section class="grid">
      <article class="card">
        <h2>Submit a support request</h2>
        <label for="customer">Customer ID</label>
        <input id="customer" value="C3001" placeholder="e.g. C3001">
        <label for="message">What does the customer need?</label>
        <textarea id="message" placeholder="Describe the issue...">I was charged twice for my subscription. Please review and refund the duplicate charge.</textarea>
        <div class="actions">
          <button id="submit" onclick="submitRequest()">Analyze request</button>
          <a class="link-button" href="/docs" target="_blank">Open API docs</a>
        </div>
      </article>
      <article class="card">
        <h2>Case lookup</h2>
        <label for="case-id">Case ID</label>
        <div class="row">
          <input id="case-id" placeholder="CASE-...">
          <button class="secondary" onclick="lookupCase()">Load case</button>
        </div>
        <label for="token">Approver token <span class="hint">(only needed for decisions)</span></label>
        <input id="token" type="password" placeholder="Stored only in this page">
        <div class="actions">
          <button id="approve-action" onclick="decide(true)" disabled>Approve action</button>
          <button id="reject-action" class="danger" onclick="decide(false)" disabled>Reject action</button>
        </div>
        <div id="case-summary" class="result">No case loaded yet.</div>
      </article>
      <article class="card wide">
        <h2>Customer details</h2>
        <p class="hint">View the customer profile, transactions, and recent support cases in a readable format.</p>
        <div class="row">
          <input id="details-customer" value="C3001" placeholder="e.g. C3001">
          <button class="secondary" onclick="loadCustomerDetails()">View customer</button>
        </div>
        <div id="customer-details" class="result">Enter a customer ID to view details.</div>
      </article>
      <article class="card wide">
        <h2>Latest response</h2>
        <div id="result" class="result">Submit a request to see the agent response.</div>
      </article>
    </section>
    <footer>Actions are simulated in this environment. No external billing system is contacted.</footer>
  </main>
  <script>
    const result = document.getElementById("result");
    const summary = document.getElementById("case-summary");
    const caseId = document.getElementById("case-id");
    const approveButton = document.getElementById("approve-action");
    const rejectButton = document.getElementById("reject-action");
    const themeToggle = document.getElementById("theme-toggle");
    function setTheme(theme) {
      document.documentElement.dataset.theme = theme;
      themeToggle.textContent = theme === "light" ? "☾ Dark" : "☀ Light";
      localStorage.setItem("supportmindai-theme", theme);
    }
    function toggleTheme() {
      setTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
    }
    setTheme(localStorage.getItem("supportmindai-theme") || "dark");
    function show(target, value) { target.textContent = typeof value === "string" ? value : String(value); }
    function statusClass(value) {
      if (["resolved", "approved"].includes(value)) return "success";
      if (["awaiting_approval", "pending"].includes(value)) return "warning";
      if (["rejected", "customer_not_found"].includes(value)) return "danger";
      return "";
    }
    function caseDetailsHtml(body) {
      const approval = body.approval_status || "not_required";
      return `<div class="case-card">
        <div class="case-field"><span>Case ID</span><strong>${escapeHtml(body.case_id)}</strong></div>
        <div class="case-field"><span>Status</span><strong class="${statusClass(body.status)}">${escapeHtml(body.status)}</strong></div>
        <div class="case-field"><span>Intent</span><strong>${escapeHtml(body.intent || "Not classified")}</strong></div>
        <div class="case-field"><span>Recommended action</span><strong>${escapeHtml(body.action || "No action")}</strong></div>
        <div class="case-field"><span>Approval</span><strong class="${statusClass(approval)}">${escapeHtml(approval)}</strong></div>
        <div class="case-field"><span>Approval required</span><strong>${body.requires_approval ? "Yes" : "No"}</strong></div>
        <div class="case-field wide"><span>Reason</span><strong>${escapeHtml(body.reason || "No additional explanation.")}</strong></div>
        <div class="case-field wide"><span>Result</span><strong>${escapeHtml(body.result || "No action has been executed.")}</strong></div>
      </div>`;
    }
    function updateDecisionControls(body) {
      const canDecide = body.status === "awaiting_approval" && body.requires_approval;
      approveButton.disabled = !canDecide;
      rejectButton.disabled = !canDecide;
    }
    function showCase(target, body) {
      target.innerHTML = caseDetailsHtml(body);
      updateDecisionControls(body);
    }
    async function request(url, options = {}) {
      const response = await fetch(url, { headers: {"Content-Type": "application/json"}, ...options });
      const body = await response.json().catch(() => ({detail: "The server returned an invalid response."}));
      if (!response.ok) throw new Error(`${response.status}: ${body.detail || "Request failed"}`);
      return body;
    }
    async function submitRequest() {
      const button = document.getElementById("submit");
      button.disabled = true;
      show(result, "Investigating customer and transaction information...");
      try {
        const body = await request("/support", {
          method: "POST",
          body: JSON.stringify({customer_id: document.getElementById("customer").value.trim(), message: document.getElementById("message").value.trim()})
        });
        caseId.value = body.case_id || "";
        showCase(result, body);
        showCase(summary, body);
      } catch (error) { show(result, error.message); }
      finally { button.disabled = false; }
    }
    async function lookupCase() {
      if (approveButton.disabled) {
        show(summary, "This case does not require an approval decision.");
        return;
      }
      if (!caseId.value.trim()) return show(summary, "Enter a case ID first.");
      try { showCase(summary, await request(`/cases/${encodeURIComponent(caseId.value.trim())}`)); }
      catch (error) {
        show(summary, error.message.includes("409")
          ? "This case is already resolved or rejected; no approval decision is pending."
          : error.message);
      }
    }
    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
      }[character]));
    }
    function customerDetailsHtml(body) {
      const customer = body.customer;
      const transactions = body.transactions;
      const cases = body.cases;
      const total = transactions.reduce((sum, item) => sum + item.amount, 0);
      const transactionRows = transactions.length ? transactions.map(item => `
        <tr><td>${escapeHtml(item.id)}</td><td>$${item.amount.toFixed(2)}</td>
        <td>${escapeHtml(item.type)}</td><td>${escapeHtml(item.status)}</td></tr>`).join("")
        : '<tr><td colspan="4" class="empty">No transactions found.</td></tr>';
      const caseRows = cases.length ? cases.map(item => `
        <tr><td>${escapeHtml(item.id)}</td><td>${escapeHtml(item.status)}</td>
        <td>${escapeHtml(item.action || "No action")}</td><td>${escapeHtml(item.approval_status)}</td></tr>`).join("")
        : '<tr><td colspan="4" class="empty">No support cases found.</td></tr>';
      return `<div class="profile">
        <div><span>Name</span><strong>${escapeHtml(customer.name)}</strong></div>
        <div><span>Customer ID</span><strong>${escapeHtml(customer.id)}</strong></div>
        <div><span>Account status</span><strong>${escapeHtml(customer.status)}</strong></div>
        <div><span>Email</span><strong>${escapeHtml(customer.email || "Not provided")}</strong></div>
        <div><span>Transactions</span><strong>${transactions.length}</strong></div>
        <div><span>Total transaction value</span><strong>$${total.toFixed(2)}</strong></div>
      </div>
      <h3>Transaction history</h3><div class="table-wrap"><table>
        <thead><tr><th>Transaction</th><th>Amount</th><th>Type</th><th>Status</th></tr></thead>
        <tbody>${transactionRows}</tbody>
      </table></div>
      <h3>Recent support cases</h3><div class="table-wrap"><table>
        <thead><tr><th>Case</th><th>Status</th><th>Action</th><th>Approval</th></tr></thead>
        <tbody>${caseRows}</tbody>
      </table></div>`;
    }
    async function loadCustomerDetails() {
      const id = document.getElementById("details-customer").value.trim();
      const target = document.getElementById("customer-details");
      if (!id) return show(target, "Enter a customer ID first.");
      try {
        const body = await request(`/customers/${encodeURIComponent(id)}/details`);
        target.innerHTML = customerDetailsHtml(body);
      } catch (error) { show(target, error.message); }
    }
    async function decide(approved) {
      if (!caseId.value.trim()) return show(summary, "Enter or create a case first.");
      try {
        const body = await request(`/cases/${encodeURIComponent(caseId.value.trim())}/approval`, {
          method: "POST",
          headers: {"Content-Type": "application/json", "X-Approver-Token": document.getElementById("token").value},
          body: JSON.stringify({approved})
        });
        showCase(summary, body); showCase(result, body);
      } catch (error) {
        show(summary, error.message.includes("409")
          ? "This case is already resolved or rejected; no approval decision is pending."
          : error.message);
      }
    }
  </script>
</body>
</html>"""


def ui_response() -> HTMLResponse:
    return HTMLResponse(content=UI_PAGE)
