const loginForm = document.getElementById("loginForm");
const messageBox = document.getElementById("message");
const loginButton = document.getElementById("loginButton");
const fieldErrors = {
  email: document.getElementById("emailError"),
  password: document.getElementById("passwordError"),
};

function clearErrors() {
  Object.entries(fieldErrors).forEach(([field, element]) => {
    const input = document.getElementById(field);
    if (input) {
      input.classList.remove("is-invalid");
    }
    element.textContent = "";
  });
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  loginButton.disabled = true;
  loginButton.textContent = "Signing in...";

  try {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    await postJson("/api/login/", { email, password });
    window.location.href = "/profile/";
  } catch (error) {
    Object.entries(error.errors || {}).forEach(([field, messages]) => {
      const input = document.getElementById(field);
      if (input) {
        input.classList.add("is-invalid");
      }
      if (fieldErrors[field]) {
        fieldErrors[field].textContent = Array.isArray(messages)
          ? messages.join(" ")
          : messages;
      }
    });
    showMessage(messageBox, error.message, "danger");
  } finally {
    loginButton.disabled = false;
    loginButton.textContent = "Sign in";
  }
});
