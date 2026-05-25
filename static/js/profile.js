const messageBox = document.getElementById("message");
const userIndicator = document.getElementById("userIndicator");
const profileContent = document.getElementById("profileContent");
const logoutButton = document.getElementById("logoutButton");
const accountStatus = document.getElementById("accountStatus");

logoutButton.addEventListener("click", async () => {
  logoutButton.disabled = true;
  logoutButton.textContent = "Logging out...";
  try {
    await postJson("/api/logout/");
    window.location.href = "/login/";
  } catch (error) {
    logoutButton.disabled = false;
    logoutButton.textContent = "Logout";
    showMessage(messageBox, error.message, "danger");
  }
});

async function loadProfile() {
  try {
    const response = await fetch("/api/me/");
    const data = await parseResponse(response);
    if (!response.ok) {
      throw new Error(data.detail || "Unable to load profile.");
    }

    document.getElementById("userEmail").textContent = data.email;
    document.getElementById("userUsername").textContent = data.username;
    userIndicator.textContent = `Signed in as ${data.email}`;
    accountStatus.textContent = data.is_active
      ? "Active"
      : "Pending verification";
    accountStatus.className = data.is_active
      ? "badge rounded-pill bg-success text-white py-2 px-3"
      : "badge rounded-pill bg-secondary text-white py-2 px-3";
    profileContent.classList.remove("d-none");
  } catch (error) {
    showMessage(messageBox, error.message, "danger");
    userIndicator.textContent = "Not signed in";
    profileContent.classList.add("d-none");
  }
}

loadProfile();
