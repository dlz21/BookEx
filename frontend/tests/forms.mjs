// Dependency-free Chrome DevTools check, launched against Django's isolated live
// test server by PatternFlyBrowserTests. Never points at the development database.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [chromePath, baseUrl, imagePath, mode] = process.argv.slice(2);
const profile = await mkdtemp(join(tmpdir(), "bookex-chrome-"));
const chrome = spawn(chromePath, [
  "--headless", "--no-sandbox", "--disable-gpu", "--no-first-run",
  "--disable-background-networking", "--disable-component-update",
  "--remote-debugging-pipe", `--user-data-dir=${profile}`, "about:blank",
], { stdio: ["ignore", "ignore", "pipe", "pipe", "pipe"] });

let sequence = 0;
let buffer = "";
let chromeErrors = "";
const pending = new Map();
const runtimeErrors = [];
const networkErrors = [];
let formPosts = 0;
chrome.stderr.on("data", (chunk) => { chromeErrors += chunk; });
chrome.on("error", (error) => {
  for (const { reject } of pending.values()) reject(error);
});
chrome.stdio[4].on("data", (chunk) => {
  buffer += chunk;
  let end;
  while ((end = buffer.indexOf("\0")) !== -1) {
    const message = JSON.parse(buffer.slice(0, end));
    buffer = buffer.slice(end + 1);
    const request = pending.get(message.id);
    if (request) {
      pending.delete(message.id);
      if (message.error) request.reject(new Error(JSON.stringify(message.error)));
      else request.resolve(message.result);
    }
    if (message.method === "Runtime.exceptionThrown") runtimeErrors.push(message.params);
    if (message.method === "Network.requestWillBeSent" && message.params.request.method === "POST") formPosts++;
    if (message.method === "Network.responseReceived") {
      const { url, status } = message.params.response;
      if (url.includes("/static/") && status >= 400) networkErrors.push({ url, status });
    }
  }
});

async function command(method, params = {}, sessionId) {
  const id = ++sequence;
  const result = new Promise((resolve, reject) => { pending.set(id, { resolve, reject }); });
  chrome.stdio[3].write(JSON.stringify({ id, method, params, sessionId }) + "\0");
  const timeout = setTimeout(() => pending.get(id)?.reject(new Error(`${method} timed out\n${chromeErrors}`)), 10000);
  try { return await result; }
  finally { clearTimeout(timeout); pending.delete(id); }
}

try {
  const { targetId } = await command("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await command("Target.attachToTarget", { targetId, flatten: true });
  const send = (method, params) => command(method, params, sessionId);
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Network.enable");
  await send("Emulation.setScriptExecutionDisabled", { value: mode === "no-js" });
  const evaluate = async (expression) => {
    const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    assert.equal(result.exceptionDetails, undefined, JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const until = async (expression) => {
    const deadline = Date.now() + 10000;
    while (Date.now() < deadline) {
      try { if (await evaluate(expression)) return; } catch { /* navigation changes contexts */ }
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    throw new Error(`Browser condition timed out: ${expression}`);
  };
  const navigate = async (path) => {
    const url = baseUrl + path;
    await send("Page.navigate", { url });
    await until(`location.href === ${JSON.stringify(url)} && document.readyState === 'complete'`);
  };
  const fill = (selector, value) => evaluate(`(() => {
    const field = document.querySelector(${JSON.stringify(selector)});
    field.value = ${JSON.stringify(value)};
    field.dispatchEvent(new Event('input', {bubbles: true}));
  })()`);
  const enter = async (selector) => {
    await evaluate(`document.querySelector(${JSON.stringify(selector)}).focus()`);
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: "\r" });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  };
  const blockedSubmission = async (submitFrom, invalidField, validityFlag) => {
    const postsBefore = formPosts;
    await enter(submitFrom);
    await until(`document.activeElement === document.querySelector(${JSON.stringify(invalidField)}) &&
      document.activeElement.validity[${JSON.stringify(validityFlag)}] &&
      document.activeElement.validationMessage.length > 0`);
    assert.equal(formPosts, postsBefore, "Invalid fields must block the POST");
  };

  await send("Emulation.setDeviceMetricsOverride", { width: 360, height: 900, deviceScaleFactor: 1, mobile: false });
  await navigate("/");
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
  assert.equal(await evaluate("document.activeElement.matches('.skip-link')"), true);
  assert.equal(await evaluate("document.activeElement.getBoundingClientRect().top >= 0"), true);
  await enter(".skip-link");
  await until("document.activeElement.id === 'main-content'");
  assert.equal(await evaluate("document.querySelector('#primary-navigation a[aria-current=page]').pathname"), "/");
  if (mode === "js") {
    await until("document.querySelector('#primary-navigation').hidden");
    await enter("#navigation-toggle");
    assert.equal(await evaluate("document.querySelector('#navigation-toggle').getAttribute('aria-expanded')"), "true");
    await evaluate("document.querySelector('#primary-navigation a').focus()");
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    assert.equal(await evaluate("document.activeElement.id"), "navigation-toggle");
    assert.equal(await evaluate("document.querySelector('#primary-navigation').hidden"), true);
    await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
    await until("document.querySelector('#navigation-toggle').hidden && !document.querySelector('#primary-navigation').hidden");
    assert.equal(await evaluate("document.activeElement.matches('#primary-navigation a')"), true);
  } else {
    assert.equal(await evaluate("document.querySelector('#navigation-toggle').hidden"), true);
    assert.equal(await evaluate("getComputedStyle(document.querySelector('#primary-navigation')).display !== 'none'"), true);
  }

  await navigate("/login/?next=/postbook");
  assert.equal(await evaluate("document.querySelector('#id_password').type"), "password");
  await until("getComputedStyle(document.querySelector('.pf-v6-c-card')).borderRadius !== '0px'");
  assert.equal(await evaluate("document.querySelector('#id_username').matches(':user-invalid')"), false);
  await blockedSubmission("#id_username", "#id_username", "valueMissing");
  assert.equal(await evaluate("document.querySelector('#id_username').matches(':user-invalid')"), true);
  await fill("#id_username", "prototype");
  assert.equal(await evaluate("document.querySelector('#id_username').matches(':user-invalid')"), false);
  await blockedSubmission("#id_username", "#id_password", "valueMissing");
  await fill("#id_password", "wrong-password");
  await enter("#id_password");
  await until("!!document.querySelector('[data-form-errors]')");
  assert.equal(await evaluate("document.querySelector('#id_username').value"), "prototype");
  assert.equal(await evaluate("document.querySelector('#id_password').value"), "");
  if (mode === "js") await until("document.activeElement.hasAttribute('data-form-errors')");
  await fill("#id_password", "Test-password-293!");
  await enter("#id_password");
  await until("location.pathname === '/postbook' && !!document.querySelector('#id_picture')");

  await fill("#id_name", "Browser prototype");
  await fill("#id_web", "invalid-url");
  await fill("#id_price", "12.50");
  await blockedSubmission("#id_web", "#id_web", "typeMismatch");
  await fill("#id_web", "https://example.com/book");
  await fill("#id_price", "12.501");
  await blockedSubmission("#id_price", "#id_price", "stepMismatch");
  await fill("#id_price", "12.50");
  await blockedSubmission("#id_price", "#id_picture", "valueMissing");

  // Deliberately bypass client constraints once to prove Django still rejects
  // malformed requests. This modifies only the test page, not application code.
  await evaluate("document.querySelector('form.pf-v6-c-form').noValidate = true");
  await enter("#id_price");
  await until("!!document.querySelector('#id_picture_error')");
  assert.equal(await evaluate("document.querySelector('#id_name').value"), "Browser prototype");
  assert.equal(await evaluate("document.querySelector('#id_picture').getAttribute('aria-invalid')"), "true");
  assert.equal(await evaluate("document.querySelector('#id_picture').getAttribute('aria-describedby')"), "id_picture_error");
  const { root } = await send("DOM.getDocument");
  const { nodeId } = await send("DOM.querySelector", { nodeId: root.nodeId, selector: "#id_picture" });
  await send("DOM.setFileInputFiles", { nodeId, files: [imagePath] });
  for (const width of [360, 768, 1280]) {
    await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: false });
    await until("document.documentElement.scrollWidth <= innerWidth");
  }
  await enter("#id_price");
  await until("location.search === '?submitted=True' && !!document.querySelector('[role=status]')");
  assert.equal(await evaluate("document.querySelector('[role=status]').textContent.includes('Book posted successfully!')"), true);
  assert.equal(await evaluate("document.querySelector('.account-actions').textContent.includes('Signed in as prototype')"), true);
  assert.equal(await evaluate("document.querySelector('#primary-navigation a[aria-current=page]').pathname"), "/postbook");
  await navigate("/displaybooks");
  assert.equal(await evaluate("document.querySelectorAll('#table-striped tbody tr').length"), 2);
  for (const width of [360, 768, 1280]) {
    await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: false });
    await until("document.documentElement.scrollWidth <= innerWidth");
    const narrow = width < 1280;
    await until(`(getComputedStyle(document.querySelector('#table-striped thead')).display === 'none') === ${narrow}`);
    assert.equal(await evaluate(`(() => {
      const [odd, even] = document.querySelectorAll('#table-striped tbody tr');
      return getComputedStyle(odd).backgroundColor !== getComputedStyle(even).backgroundColor;
    })()`), true, "Alternating rows must have different backgrounds");
    if (narrow) {
      assert.equal(await evaluate("getComputedStyle(document.querySelector('[data-label=\"Posted Date\"]'), '::before').content"), '"Posted Date"');
    }
  }
  assert.equal(await evaluate("[...document.querySelectorAll('#table-striped tbody a')].every(a => a.pathname.startsWith('/book_detail/'))"), true);
  await enter(".account-actions button");
  await until("location.pathname === '/' && !!document.querySelector('.account-actions a[href=\"/register\"]')");
  assert.deepEqual(runtimeErrors, []);
  assert.deepEqual(networkErrors, []);
  console.log(`PASS (${mode}): shell, native forms/upload, striped table, responsive labels and long titles at 360/768/1280px`);
} finally {
  await command("Browser.close").catch(() => {});
  chrome.kill();
  // Chrome may still be flushing its temporary profile after Browser.close.
  if (chrome.exitCode === null) await new Promise((resolve) => chrome.once("exit", resolve));
  await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
}
