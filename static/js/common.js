function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return "";
}

function showMessage(element, text, type) {
  element.textContent = text;
  element.className = `alert alert-${type}`;
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return { detail: "Unexpected server response. Please try again." };
}

function getErrorMessage(data) {
  if (data.detail) {
    return data.detail;
  }
  if (data.non_field_errors) {
    return data.non_field_errors.join(" ");
  }
  return "Please correct the highlighted fields.";
}

async function apiFetch(url, options = {}) {
  const requestOptions = {
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      ...(options.headers || {}),
    },
    ...options,
  };

  let response = await fetch(url, requestOptions);
  let didRetry = false;

  if (response.status === 401 && url !== "/api/token/refresh/" && !didRetry) {
    const refreshResponse = await fetch("/api/token/refresh/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
    });

    if (refreshResponse.ok) {
      didRetry = true;
      response = await fetch(url, requestOptions);
    }
  }

  return response;
}

async function getJson(url) {
  const response = await apiFetch(url, { method: "GET" });
  const data = await parseResponse(response);
  if (!response.ok) {
    const error = new Error(getErrorMessage(data));
    error.errors = data;
    throw error;
  }
  return data;
}

async function postJson(url, payload = {}) {
  const response = await apiFetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    const error = new Error(getErrorMessage(data));
    error.errors = data;
    throw error;
  }
  return data;
}
