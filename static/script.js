document.addEventListener("DOMContentLoaded", (event) => {
  const configPanel = document.getElementById("config-panel");
  const configToggle = document.getElementById("config-toggle");

  configToggle.addEventListener("click", toggleConfigPanel);

  document.addEventListener("click", function (event) {
    var isClickInsideConfigPanel = configPanel.contains(event.target);
    var isClickInsideConfigToggle = configToggle.contains(event.target);

    if (
      !isClickInsideConfigPanel &&
      !isClickInsideConfigToggle &&
      configPanel.style.left === "0px"
    ) {
      toggleConfigPanel(); // Close the panel
    }
  });
});

function handleRefresh(event) {
  event.preventDefault(); // Prevent default form submission

  // Gather form data
  const formData = new FormData();
  formData.append("radarr_url", document.getElementById("radarr_url").value);
  formData.append(
    "radarr_api_key",
    document.getElementById("radarr_api_key").value
  );
  // ... add other form elements ...

  // Send data using fetch
  fetch("/", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (response.ok) {
        checkServerStatusAndRefreshFolders();
      } else {
        console.error("Form submission failed");
      }
    })
    .catch((error) => console.error("Error:", error));
}

function handleSubmit(event) {
  event.preventDefault(); // Prevent default form submission

  // Display a loading message
  displayLoadingMessage();

  // Gather form data
  const formData = new FormData(document.querySelector("form"));

  // Send data using fetch
  fetch("/", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (response.ok) {
        waitForServerReady(); // Wait for server to be ready then reload the page
      } else {
        console.error("Form submission failed");
      }
    })
    .catch((error) => console.error("Error:", error));
}

function displayLoadingMessage() {
  // Add a loading message to the page
  let loadingDiv = document.createElement("div");
  loadingDiv.id = "loadingMessage";
  loadingDiv.style.position = "fixed";
  loadingDiv.style.top = "50%";
  loadingDiv.style.left = "50%";
  loadingDiv.style.transform = "translate(-50%, -50%)";
  loadingDiv.style.fontSize = "1.5rem";
  loadingDiv.innerText = "Configuration is updating. Please wait...";
  document.body.appendChild(loadingDiv);
}

function waitForServerReady() {
  fetch("/server_status")
    .then((response) => {
      if (response.ok) {
        window.location.reload(); // Reload the page
      } else {
        setTimeout(waitForServerReady, 1000); // Retry after 1 second
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      setTimeout(waitForServerReady, 1000);
    });
}

function markdownToHTML(text) {
  // Convert italics
  let htmlText = text.replace(/\*([^\*]+)\*/g, "<em>$1</em>");

  // Convert bullet points with indentation
  htmlText = htmlText.replace(
    /^- (.+)$/gm,
    "<li style='margin-left: 20px;'>$1</li>"
  );
  htmlText = "<ul>" + htmlText + "</ul>"; // Wrap with <ul> tag

  return htmlText;
}

function checkServerStatusAndRefreshFolders() {
  fetch("/server_status")
    .then((response) => {
      if (response.ok) {
        // Server is ready, now refresh Radarr root folders
        fetchRadarrRootFolders();
      } else {
        setTimeout(checkServerStatusAndRefreshFolders, 1000); // Retry after 1 second
      }
    })
    .catch((error) => {
      console.error("Error checking server status:", error);
      setTimeout(checkServerStatusAndRefreshFolders, 1000); // Retry after 1 second
    });
}

function waitForServerReady() {
  fetch("/server_status")
    .then((response) => {
      if (response.ok) {
        // Server is ready, reset UI
        resetUI();
      } else {
        // Retry after a delay
        setTimeout(waitForServerReady, 3000); // Retry after 3 seconds
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      setTimeout(waitForServerReady, 3000);
    });
}

function resetUI() {
  // Hide loading indicator
  document.getElementById("loadingIndicator").style.display = "none";
  // Enable submit button
  document.getElementById("submitBtn").disabled = false;
}

function fetchRadarrRootFolders() {
  let radarrUrl = document.getElementById("radarr_url").value;
  let radarrApiKey = document.getElementById("radarr_api_key").value;

  if (radarrUrl && radarrApiKey) {
    fetch(
      `/fetch_root_folders?radarr_url=${encodeURIComponent(
        radarrUrl
      )}&radarr_api_key=${encodeURIComponent(radarrApiKey)}`
    )
      .then((response) => response.json())
      .then((data) => {
        let rootFolderSelect = document.getElementById("radarrRootFolder");
        rootFolderSelect.innerHTML = ""; // Clear existing options

        data.forEach((folder) => {
          let option = document.createElement("option");
          option.value = folder.path;
          option.textContent = folder.path;
          rootFolderSelect.appendChild(option);
        });
      })
      .catch((error) => console.error("Error:", error));
  }
}

async function loadChannels() {
  let token = document.getElementById("discord_token").value;
  if (token) {
    let response = await fetch("/channels?token=" + encodeURIComponent(token));
    if (response.ok) {
      let channels = await response.json();
      console.log("Here is the json object I think:", channels);
      let channelSelect = document.getElementById("discord_channel");
      channelSelect.innerHTML = "";

      channels.forEach((channel) => {
        let option = document.createElement("option");
        option.value = channel.id;
        option.textContent = channel.name;
        console.log("Channel name: ", channel.name);
        console.log("Channel id: ", channel.id);
        channelSelect.appendChild(option);
      });
      channelSelect.disabled = false;
    }
  }
}

function handleKeyPress(event) {
  if (event.keyCode === 13) {
    // 13 is the Enter key
    event.preventDefault(); // Prevent default to avoid form submit
    sendMessage();
  }
}

function toggleConfigPanel() {
  var configPanel = document.getElementById("config-panel");
  if (configPanel.style.left === "0px") {
    configPanel.style.left = "-250px"; // Hide the panel
  } else {
    configPanel.style.left = "0px"; // Show the panel
  }
}

function sendMessage() {
  let messageInput = document.getElementById("message-input");
  let message = messageInput.value;
  updateChat("user", message);

  // Clear the input box right after sending the message
  messageInput.value = "";

  fetch("/send_message", {
    method: "POST",
    body: JSON.stringify({ message: message }),
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      updateChat("bot", data.response);
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function refreshDiscordChannels() {
  let token =
    document.getElementById("discord_token").value ||
    '{{ config["discord_token"] }}';
  if (token) {
    // Existing code to load channels
    loadChannels();
  } else {
    alert("Please enter a Discord token.");
  }
}

function checkAndFetchRootFolders() {
  let radarrUrl = document.getElementById("radarr_url").value;
  let radarrApiKey = document.getElementById("radarr_api_key").value;

  if (radarrUrl && radarrApiKey) {
    fetchRadarrRootFolders();
  }
}

// Function to update the chat with new messages and initialize popovers
function updateChat(sender, text) {
  let chatBox = document.getElementById("chat-box");
  let messageDiv = document.createElement("div");
  messageDiv.classList.add("message");

  let senderSpan = document.createElement("span");
  senderSpan.classList.add(sender === "user" ? "sender-user" : "sender-bot");
  senderSpan.textContent = sender === "user" ? "You: " : "Bot: ";

  let textDiv = document.createElement("div");
  textDiv.classList.add("text-content");
  let htmlContent = markdownToHTML(text);
  textDiv.innerHTML = htmlContent;

  messageDiv.appendChild(senderSpan);
  messageDiv.appendChild(textDiv);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  $(messageDiv)
    .find('[data-toggle="popover"]')
    .each(function () {
      setupPopoverHideWithDelay(this);
    });
}

// Function to add a movie to Radarr and update the chat
function addMovieToRadarr(tmdbId) {
  fetch(`/add_movie_to_radarr/${tmdbId}`)
    .then((response) => response.json())
    .then((data) => {
      updateChat("bot", data.message);
    })
    .catch((error) => console.error("Error:", error));
}

// Updated function for setupPopoverHideWithDelay
function setupPopoverHideWithDelay(element) {
  var hideDelay = 200; // Delay in milliseconds
  var hideDelayTimer = null;

  var showPopover = function () {
    clearTimeout(hideDelayTimer);
    closeAllPopovers(); // Close all other open popovers

    var $element = $(element);
    var tmdbId = $element.data("tmdb-id");

    // Display "Loading details" message
    $element.popover("show");
    var loadingContent =
      '<div class="loading-content">Loading details...</div>';
    $element.data("bs.popover").config.content = loadingContent;

    // Function to update the popover content once details are loaded
    // Function to update the popover content once details are loaded
    var updatePopoverContent = function (data) {
      var contentHtml = `
    <div class="movie-details-card">
      <div class="movie-poster">
        <img src="https://image.tmdb.org/t/p/original${
          data.poster_path
        }" alt="${data.title} Poster" class="img-fluid">
      </div>
      <div class="movie-info">
        <h5 class="movie-title">${data.title}</h5>
        <p class="movie-director"><strong>Director:</strong> ${
          data.director || "N/A"
        }</p>
        <p class="movie-actors"><strong>Main Actors:</strong> ${
          data.actors ? data.actors.join(", ") : "N/A"
        }</p>
        
        <p class="movie-release-date"><strong>Release Date:</strong> ${
          data.release_date
        }</p>
        <p class="movie-rating"><strong>Rating:</strong> ${
          data.vote_average
        }</p>
        <p class="movie-description">${data.overview}</p>
      </div>
    </div>`;
      $(element).data("bs.popover").config.content = contentHtml;
      $(element).popover("show");
    };

    // Load movie details
    $.get(`/movie_details/${tmdbId}`, function (data) {
      updatePopoverContent(data); // Update the popover content
    }).fail(function () {
      $element.data("bs.popover").config.content = "Failed to load details.";
      $element.popover("show"); // Show the failed message
    });
  };

  var hidePopover = function () {
    clearTimeout(hideDelayTimer);
    hideDelayTimer = setTimeout(function () {
      $(element).popover("hide");
    }, hideDelay);
  };

  $(element)
    .popover({
      trigger: "manual",
      html: true,
      placement: "right",
      container: "body",
      content: "Loading details...",
      delay: { show: 100, hide: hideDelay },
    })
    .on("mouseenter", showPopover)
    .on("mouseleave", hidePopover);

  $("body")
    .on("mouseenter", ".popover", function () {
      clearTimeout(hideDelayTimer);
    })
    .on("mouseleave", ".popover", function () {
      hidePopover();
    });
}

// Function to close all open popovers
function closeAllPopovers() {
  $('[data-toggle="popover"]').each(function () {
    $(this).popover("hide");
  });
}

// Initialize popovers for each movie link
$(document).ready(function () {
  $('[data-toggle="popover"]').each(function () {
    setupPopoverHideWithDelay(this);
  });
});
