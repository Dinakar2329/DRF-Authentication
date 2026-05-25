const registerForm = document.getElementById("registerForm");
const verifyForm = document.getElementById("verifyForm");
const messageBox = document.getElementById("message");
const modalMessageBox = document.getElementById("modalMessage");
const registerButton = document.getElementById("registerButton");
const verifyButton = document.getElementById("verifyButton");
const otpHint = document.getElementById("otpHint");
const otpInputs = Array.from(document.querySelectorAll(".otp-input"));
const otpModal = new bootstrap.Modal(document.getElementById("otpModal"));
const fieldErrors = {
  email: document.getElementById("emailError"),
  password: document.getElementById("passwordError"),
  otp: document.getElementById("otpError"),
};

function clearModalMessage() {
  modalMessageBox.textContent = "";
  modalMessageBox.className = "alert d-none";
}

function clearErrors() {
  Object.entries(fieldErrors).forEach(([field, element]) => {
    const input = document.getElementById(field);
    if (input) {
      input.classList.remove("is-invalid");
    }
    element.textContent = "";
  });
  otpInputs.forEach((input) => input.classList.remove("is-invalid"));
}

function showFieldErrors(errors) {
  Object.entries(errors).forEach(([field, messages]) => {
    if (!fieldErrors[field]) {
      return;
    }
    const input = document.getElementById(field);
    if (input) {
      input.classList.add("is-invalid");
    }
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

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  registerButton.disabled = true;
  registerButton.textContent = "Sending...";

  try {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const data = await postJson("/api/register/", { email, password });

    showMessage(messageBox, data.message, "success");
    otpHint.classList.remove("d-none");
    clearOtpInputs();
    clearModalMessage();
    otpModal.show();
    setTimeout(() => otpInputs[0].focus(), 250);
  } catch (error) {
    showFieldErrors(error.errors || {});
    showMessage(messageBox, error.message, "danger");
  } finally {
    registerButton.disabled = false;
    registerButton.textContent = "Send verification code";
  }
});

verifyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  clearModalMessage();
  verifyButton.disabled = true;
  verifyButton.textContent = "Verifying...";

  try {
    const email = document.getElementById("email").value.trim();
    const otp = getOtpValue();
    const data = await postJson("/api/register/verify/", { email, otp });

    showMessage(messageBox, data.message, "success");
    otpModal.hide();
    otpHint.classList.add("d-none");
    clearOtpInputs();
    registerForm.reset();
  } catch (error) {
    showFieldErrors(error.errors || {});
    showMessage(modalMessageBox, error.message, "danger");
  } finally {
    verifyButton.disabled = false;
    verifyButton.textContent = "Verify account";
  }
});
