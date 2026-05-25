const registerForm = document.getElementById("registerForm");
const verifyForm = document.getElementById("verifyForm");
const messageBox = document.getElementById("message");
const modalMessageBox = document.getElementById("modalMessage");
const registerButton = document.getElementById("registerButton");
const verifyButton = document.getElementById("verifyButton");
const otpInputs = Array.from(document.querySelectorAll(".otp-input"));
const otpModal = new bootstrap.Modal(document.getElementById("otpModal"));
const fieldErrors = {
  email: document.getElementById("emailError"),
  password: document.getElementById("passwordError"),
  otp: document.getElementById("otpError"),
};
const openVerifyModalButton = document.getElementById("openVerifyModalButton");
const resendModal = new bootstrap.Modal(document.getElementById("resendModal"));
const resendForm = document.getElementById("resendForm");
const resendEmailInput = document.getElementById("resendEmail");
const resendEmailError = document.getElementById("resendEmailError");
const resendModalMessage = document.getElementById("resendModalMessage");
const resendSubmitButton = document.getElementById("resendSubmitButton");

// Tracks which email to use when the OTP verify form submits.
// Set by whichever flow triggered the OTP modal.
let pendingVerifyEmail = "";

function clearModalMessage() {
  modalMessageBox.textContent = "";
  modalMessageBox.className = "alert d-none";
}

function clearResendErrors() {
  resendEmailInput.classList.remove("is-invalid");
  resendEmailError.textContent = "";
  resendModalMessage.textContent = "";
  resendModalMessage.className = "alert d-none";
}

function showResendMessage(text, type) {
  resendModalMessage.textContent = text;
  resendModalMessage.className = `alert alert-${type}`;
}

function clearErrors() {
  Object.entries(fieldErrors).forEach(([field, element]) => {
    const input = document.getElementById(field);
    if (input) input.classList.remove("is-invalid");
    element.textContent = "";
  });
  otpInputs.forEach((input) => input.classList.remove("is-invalid"));
}

function showFieldErrors(errors) {
  Object.entries(errors).forEach(([field, messages]) => {
    if (!fieldErrors[field]) return;
    const input = document.getElementById(field);
    if (input) input.classList.add("is-invalid");
    if (field === "otp") {
      otpInputs.forEach((otpInput) => otpInput.classList.add("is-invalid"));
    }
    fieldErrors[field].textContent = Array.isArray(messages)
      ? messages.join(" ")
      : messages;
  });
}

function getOtpValue() {
  return otpInputs.map((input) => input.value).join("");
}

function clearOtpInputs() {
  otpInputs.forEach((input) => {
    input.value = "";
  });
}

function openOtpModal() {
  clearOtpInputs();
  clearModalMessage();
  otpModal.show();
  setTimeout(() => otpInputs[0].focus(), 250);
}

// ── OTP input behaviour ──────────────────────────────────────────────────────

otpInputs.forEach((input, index) => {
  input.addEventListener("input", () => {
    input.value = input.value.replace(/\D/g, "").slice(0, 1);
    if (input.value && otpInputs[index + 1]) {
      otpInputs[index + 1].focus();
    }
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Backspace" && !input.value && otpInputs[index - 1]) {
      otpInputs[index - 1].focus();
    }
  });

  input.addEventListener("paste", (event) => {
    event.preventDefault();
    const pasted = event.clipboardData
      .getData("text")
      .replace(/\D/g, "")
      .slice(0, 6);
    pasted.split("").forEach((digit, digitIndex) => {
      otpInputs[digitIndex].value = digit;
    });
    const nextIndex = Math.min(pasted.length, otpInputs.length - 1);
    otpInputs[nextIndex].focus();
  });
});

// ── Flow 1: Register (new user) ──────────────────────────────────────────────

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  registerButton.disabled = true;
  registerButton.textContent = "Sending…";

  try {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const data = await postJson("/api/register/", { email, password });

    pendingVerifyEmail = email;
    showMessage(messageBox, data.message, "success");
    openOtpModal();
  } catch (error) {
    showFieldErrors(error.errors || {});
    showMessage(messageBox, error.message, "danger");
  } finally {
    registerButton.disabled = false;
    registerButton.textContent = "Send verification code";
  }
});

// ── Flow 2: "Verify account" button (already registered, not yet verified) ──
//
// Opens the resend modal so the user can enter their email.
// The resend submit handler below then calls the backend, gets a fresh OTP,
// and transitions to the OTP modal automatically.

openVerifyModalButton.addEventListener("click", () => {
  clearResendErrors();

  // Pre-fill email from the register form if the user already typed it.
  const typedEmail = document.getElementById("email").value.trim();
  if (typedEmail) resendEmailInput.value = typedEmail;

  resendModal.show();
});

// ── Resend / send-code modal ─────────────────────────────────────────────────

resendForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearResendErrors();
  resendSubmitButton.disabled = true;
  resendSubmitButton.textContent = "Sending…";

  const email = resendEmailInput.value.trim();
  if (!email) {
    resendEmailInput.classList.add("is-invalid");
    resendEmailError.textContent = "Enter your email address.";
    resendSubmitButton.disabled = false;
    resendSubmitButton.textContent = "Send code";
    return;
  }

  try {
    const data = await postJson("/api/register/resend/", { email });

    pendingVerifyEmail = email;
    showMessage(messageBox, data.message, "success");

    // Close the email-prompt modal, then open the OTP modal.
    resendModal.hide();
    // Small delay so Bootstrap can finish the hide animation first.
    setTimeout(() => openOtpModal(), 300);
  } catch (error) {
    if (error.errors?.email) {
      resendEmailInput.classList.add("is-invalid");
      resendEmailError.textContent = Array.isArray(error.errors.email)
        ? error.errors.email.join(" ")
        : error.errors.email;
    }
    showResendMessage(error.message, "danger");
  } finally {
    resendSubmitButton.disabled = false;
    resendSubmitButton.textContent = "Send code";
  }
});

// ── OTP verification ─────────────────────────────────────────────────────────

verifyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  clearModalMessage();
  verifyButton.disabled = true;
  verifyButton.textContent = "Verifying…";

  try {
    // Use the email captured at OTP-send time; fall back to register field.
    const email =
      pendingVerifyEmail || document.getElementById("email").value.trim();
    const otp = getOtpValue();
    const data = await postJson("/api/register/verify/", { email, otp });

    showMessage(messageBox, data.message, "success");
    otpModal.hide();
    clearOtpInputs();
    registerForm.reset();
    pendingVerifyEmail = "";
  } catch (error) {
    showFieldErrors(error.errors || {});
    showMessage(modalMessageBox, error.message, "danger");
  } finally {
    verifyButton.disabled = false;
    verifyButton.textContent = "Verify account";
  }
});
