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

// Track the last mouse position
let lastMousePosition = { x: 0, y: 0 };

$(document).on("mousemove", ".movie-title", function (event) {
  lastMousePosition = { x: event.pageX, y: event.pageY };
});

function getMouseRelativePosition(event, element) {
  const rect = element.getBoundingClientRect();
  const relativeX = event.clientX - rect.left;
  const relativeY = event.clientY - rect.top;
  return { relativeX, relativeY, rect };
}

// Function to split the text of each .movie-title element into individual spans for each word
function splitTextIntoSpans() {
  $(".movie-title").each(function () {
    const words = $(this).text().split(" ");
    $(this).empty();
    words.forEach((word) => {
      $(this).append($("<span>").text(word + " "));
    });
  });
}

// Track the last mouse event
let lastMouseEvent = null;

$(document).on("mouseenter", ".movie-title", function (event) {
  // Get the text of the movie title
  const text = $(this).text();

  // Split the text into words
  const words = text.split(" ");

  // Create a temporary span for each word and measure its position and size
  const wordPositions = words.map((word, index) => {
    const $span = $("<span>").text(word).appendTo(this);
    const position = $span.position();
    const width = $span.width();
    $span.remove();
    return { index, left: position.left, right: position.left + width };
  });

  // Determine which word the mouse is over
  const mouseX = event.pageX - $(this).offset().left;
  const word = wordPositions.find(
    (pos) => mouseX >= pos.left && mouseX <= pos.right
  );

  // Store the word index and position in data attributes
  $(this).data("word-index", word.index);
  $(this).data("word-position", word.left);
});

function customPopoverPlacement(context, source) {
  const wordPosition = $(source).data("word-position");
  const triggerRect = source.getBoundingClientRect();
  const popoverHeight = $(context).outerHeight();
  const windowHeight = window.innerHeight;

  const spaceTop = triggerRect.top;
  const spaceBottom = windowHeight - triggerRect.bottom;

  // Check if the popover fits on top or bottom, is not off the viewport, and doesn't cover the source
  const fitsTop = spaceTop >= popoverHeight;
  const fitsBottom = spaceBottom >= popoverHeight;

  // Determine the placement based on the word position
  const placement = wordPosition < triggerRect.width / 2 ? "bottom" : "top";

  // Create an array of placements that can fit the popover
  const placements = [
    { side: placement, space: fitsBottom ? spaceBottom : 0 },
    {
      side: placement === "bottom" ? "top" : "bottom",
      space: fitsTop ? spaceTop : 0,
    },
  ];

  // Filter out placements that would cover the source
  const validPlacements = placements.filter((placement) => placement.space > 0);

  // If there are no valid placements, default to the calculated placement
  if (validPlacements.length === 0) {
    return placement;
  }

  // Sort the placements by the available space
  validPlacements.sort((a, b) => b.space - a.space);

  // Return the placement with the most space
  return validPlacements[0].side;
}

// Updated function for setupPopoverHideWithDelay
function setupPopoverHideWithDelay(element) {
  var hideDelay = 100; // Delay in milliseconds
  var hideDelayTimer = null;

  // Function to update the popover content once details are loaded
  function updatePopoverContent(data) {
    var contentHtml = `
      <div class="movie-title">${data.title}</div>
      <div class="movie-details-card">
        <div class="movie-poster">
          <img src="https://image.tmdb.org/t/p/original${data.poster_path}" alt="${data.title} Poster" class="img-fluid">
        </div>
        <div class="movie-info">
          
          <p class="movie-director"><strong>Director:</strong> ${data.director}</p>
          <p class="movie-dop"><strong>DoP:</strong> ${data.dop}</p>
          <p class="movie-writers"><strong>Writers:</strong> ${data.writers}</p>
          <p class="movie-stars"><strong>Stars:</strong> ${data.stars}</p>
          <p class="movie-rating"><strong>Rating:</strong> ${data.vote_average}</p>
          <p class="movie-release-date"><strong>Release Date:</strong> ${data.release_date}</p>
          <p class="movie-description">${data.description}</p>
        </div>
      </div>`;
    $(element).data("bs.popover").config.content = contentHtml;
    $(element).popover("show");
    $(element).popover("update");
  }

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

    // Load movie details
    $.get(`/movie_details/${tmdbId}`, function (data) {
      updatePopoverContent(data); // Update the popover content
    }).fail(function () {
      $element.data("bs.popover").config.content = "Failed to load details.";
      $element.popover("show");
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
      placement: function (context, source) {
        return customPopoverPlacement(context, source);
      },
      container: "body",
      content: "Loading details...",
      offset: 10,
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

$(document).ready(splitTextIntoSpans);
$(window).resize(splitTextIntoSpans);
