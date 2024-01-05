$.fn.popover.Constructor.Default.whiteList.button = [];
$.fn.popover.Constructor.Default.whiteList.button.push("type");
$.fn.popover.Constructor.Default.whiteList.button.push("class");
$.fn.popover.Constructor.Default.whiteList.dl = [];
$.fn.popover.Constructor.Default.whiteList.dt = [];
$.fn.popover.Constructor.Default.whiteList.dd = [];

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
        setTimeout(waitForServerReady, 350); // Retry after 3 seconds
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      setTimeout(waitForServerReady, 350);
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
    configPanel.style.left = "-3000px"; // Hide the panel
  } else {
    configPanel.style.left = "0px"; // Show the panel
  }
}

function sendMessage() {
  let messageInput = document.getElementById("message-input");
  let message = messageInput.value;

  // Update chat with user's message
  updateChat("user", message);

  // Show loading message in chat
  displayChatLoadingMessage();

  fetch("/send_message", {
    method: "POST",
    body: JSON.stringify({ message: message }),
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      // Hide loading message and update chat with bot's response
      hideChatLoadingMessage();
      updateChat("bot", data.response);
    })
    .catch((error) => {
      console.error("Error:", error);
      hideChatLoadingMessage();
    });

  // Clear the input box right after sending the message
  messageInput.value = "";
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

  let movieTitleElement = document.createElement("span");
  movieTitleElement.className = "movie-title";
  movieTitleElement.textContent = "Your Movie Title Here";

  $(messageDiv)
    .find('[data-toggle="popover"]')
    .each(function () {
      setupPopoverHideWithDelay(this);
    });
}

function displayChatLoadingMessage() {
  let chatBox = document.getElementById("chat-box");
  let loadingDiv = document.createElement("div");
  loadingDiv.id = "chatLoadingMessage";
  loadingDiv.classList.add("message");

  let botLabelSpan = document.createElement("span");
  botLabelSpan.classList.add("sender-bot");
  botLabelSpan.textContent = "Bot:";
  botLabelSpan.style.marginRight = "12px"; // Set right margin for spacing

  let loadingAnimationSpan = document.createElement("span");
  loadingAnimationSpan.classList.add("loading-animation");

  loadingDiv.appendChild(botLabelSpan);
  loadingDiv.appendChild(loadingAnimationSpan);

  chatBox.appendChild(loadingDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function hideChatLoadingMessage() {
  let loadingDiv = document.getElementById("chatLoadingMessage");
  if (loadingDiv) {
    loadingDiv.remove();
  }
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

$(document).on("mousemove", ".movie-title", function (event) {
  lastMousePosition = { x: event.pageX, y: event.pageY };
});

function sendPredefinedMessage(message) {
  updateChat("user", message);
  displayChatLoadingMessage();

  fetch("/send_message", {
    method: "POST",
    body: JSON.stringify({ message: message }),
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      hideChatLoadingMessage();
      updateChat("bot", data.response);
    })
    .catch((error) => {
      hideChatLoadingMessage();
      console.error("Error:", error);
    });
}

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
  var hideDelay = 200; // Delay in milliseconds
  var hideDelayTimer = null;
  var isMouseOverPopover = false; // New variable to track if the mouse is over the popover

  // Function to update the popover content once details are loaded
  function updatePopoverContent(data) {
    function createPersonSpans(names, group) {
      const maxDisplay = 3; // Number of names to display initially
      let displayedNamesHtml = names
        .slice(0, maxDisplay)
        .map((name) => `<span class="person-link">${name.trim()}</span>`)
        .join(", ");

      let hiddenNamesHtml = "";
      if (names.length > maxDisplay) {
        hiddenNamesHtml = names
          .slice(maxDisplay)
          .map(
            (name) =>
              `<span class="person-link" style="display: none;">${name.trim()}</span>`
          )
          .join(", ");
      }

      let moreButtonHtml =
        names.length > maxDisplay
          ? `<span id="toggle-${group}" class="more-toggle">More</span>`
          : "";

      return `<span id="displayed-${group}">${displayedNamesHtml}</span><span id="more-${group}" style="display: none;">${hiddenNamesHtml}</span>${moreButtonHtml}`;
    }
    console.log("Here is the data:", data);
    console.log("Here is the imdb_id: ", data.imdb_id);
    console.log("Here is the wiki_url: ", data.wiki_url);
    var buttonsHtml = `
      <div style="text-align: right; padding-top: 10px; display: flex; justify-content: flex-end;">
        <button type="button" class="btn popover-button">Add to Radarr </button>
        <button type="button" class="btn popover-button">Ask MovieBot</button>
        <button type="button" class="btn popover-button btn-imdb" data-imdb-id="${data.imdb_id}" style="margin-left: 5px;">IMDb</button>
        <button type="button" class="btn popover-button btn-wiki" data-wiki-url="${data.wiki_url}" style="margin-left: 5px;">Wiki</button>
      </div>`;

    var contentHtml = `
      <div class="movie-title">${data.title}</div>
      <div class="movie-details-card">
        <div class="movie-poster">
          <img src="https://image.tmdb.org/t/p/original${
            data.poster_path
          }" alt="${data.title} Poster" class="img-fluid">
        </div>
        <div class="movie-info">
          <p class="movie-director"><strong>Director: </strong>${createPersonSpans(
            data.director.split(","),
            "director"
          )}</p>
          <p class="movie-dop"><strong>DoP: </strong>${createPersonSpans(
            data.dop.split(","),
            "dop"
          )}</p>
          <p class="movie-writers"><strong>Writers: </strong>${createPersonSpans(
            data.writers.split(","),
            "writers"
          )}</p>
          <p class="movie-stars"><strong>Stars: </strong>${createPersonSpans(
            data.stars.split(","),
            "stars"
          )}</p>
          <p class="movie-rating"><strong>TMDb Rating: </strong>${
            data.vote_average
          }</p>
          <p class="movie-release-date"><strong>Release Date: </strong>${
            data.release_date
          }</p>
          <p class="movie-description"><strong>Description: </strong>${
            data.description
          }</p>
          <div style="display: flex;">
            ${buttonsHtml}

          </div>
        </div>
        
      </div>`;
    $(element).data("bs.popover").config.content = contentHtml;
    $(element).popover("show");
    $(element).popover("update");

    $(".btn-wiki").attr("data-wiki-url", data.wiki_url);
    $(".btn-imdb").attr("data-imdb-id", data.imdb_id);

    // Setup mouseover event for each person link
    $(".person-link").on("mouseover", function () {
      showPersonPopover(this);
    });
  }

  $(document).on("click", ".popover-button", function () {
    // Handle the button click event
    console.log("Popover button clicked");
    // Add your custom logic here
  });

  $(document).on("click", ".btn-wiki", function () {
    var wikiUrl = $(this).data("wiki-url");
    if (wikiUrl) {
      window.open(wikiUrl, "_blank");
    } else {
      console.log("Wikipedia URL not found");
    }
  });

  var lastMousePosition = { x: 0, y: 0 };

  // Track mouse position
  $(document).on("mousemove", function (event) {
    lastMousePosition.x = event.pageX;
    lastMousePosition.y = event.pageY;
  });

  var showPopover = function () {
    clearTimeout(hideDelayTimer);
    closeAllPopovers(); // Close all other open popovers

    var $element = $(element);
    var tmdbId = $element.data("tmdb-id");

    // Display "Loading details" message
    //$element.popover("show");

    // Load movie details
    $.get(`/movie_details/${tmdbId}`, function (data) {
      updatePopoverContent(data); // Update the popover content
    }).fail(function () {
      $element.data("bs.popover").config.content = "Failed to load details.";
      $element.popover("show");
    });
  };

  // Updated hidePopover function
  var hidePopover = function () {
    if (!isMouseOverPopover) {
      var popover = $(element).data("bs.popover").getTipElement();
      var popoverRect = popover.getBoundingClientRect();
      var buffer = 10; // 10 pixels buffer

      // Check if the mouse is within the buffer area around the popover
      if (
        lastMousePosition.x < popoverRect.left - buffer ||
        lastMousePosition.x > popoverRect.right + buffer ||
        lastMousePosition.y < popoverRect.top - buffer ||
        lastMousePosition.y > popoverRect.bottom + buffer
      ) {
        $(element).popover("hide");
      } else {
        setTimeout(hidePopover, 100); // Check again after a short delay
      }
    }
  };

  // When mouse enters the popover, set isMouseOverPopover to true
  $("body").on("mouseenter", ".popover", function () {
    isMouseOverPopover = true;
  });

  // When mouse leaves the popover, set isMouseOverPopover to false and start the hide delay
  $("body").on("mouseleave", ".popover", function () {
    isMouseOverPopover = false;
    hideDelayTimer = setTimeout(hidePopover, hideDelay);
  });

  $(document).on("click", ".btn-imdb", function () {
    var imdbId = $(this).data("imdb-id");
    if (imdbId) {
      window.open(`https://www.imdb.com/title/tt${imdbId}`, "_blank");
    } else {
      console.log("IMDb ID not found");
    }
  });

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
      delay: { show: 1, hide: hideDelay },
    })
    .on("mouseenter", function () {
      var $element = $(this);
      var elementRect = this.getBoundingClientRect();

      setTimeout(function () {
        // Check if the current mouse position is within the bounds of the source element
        if (
          lastMousePosition.x >= elementRect.left &&
          lastMousePosition.x <= elementRect.right &&
          lastMousePosition.y >= elementRect.top &&
          lastMousePosition.y <= elementRect.bottom
        ) {
          showPopover.call($element); // Show the popover
        }
      }, 100); // 500 milliseconds delay
    })
    .on("mouseleave", function () {
      hideDelayTimer = setTimeout(hidePopover, hideDelay);
    });

  $("body").on("mouseenter", ".popover", function () {
    isMouseOverPopover = true;
  });

  $(document).on("click", ".more-toggle", function () {
    let group = this.id.split("-")[1];
    let moreSpan = $(`#more-${group}`);

    // Toggle the visibility
    moreSpan.toggle();

    // Update button text based on the visibility of moreSpan
    $(this).text(moreSpan.is(":visible") ? "Less" : "More");
  });
}

var popoverTimeout;

function showPersonPopover(element) {
  var popoverTimeout;
  var isMouseOverPopover = false;

  // Initialize the popover
  if (!$(element).data("bs.popover")) {
    $(element).popover({
      trigger: "manual",
      placement: "auto",
      title: "Person Details",
      content: "Loading details...",
      html: true,
    });
  }

  // Click event to show popover
  $(element)
    .off("click")
    .on("click", function () {
      var personName = $(element).text().trim();
      fetch(`/person_details/${encodeURIComponent(personName)}`)
        .then((response) => response.json())
        .then((data) => {
          var imagePath = data.profile_path
            ? `https://image.tmdb.org/t/p/original${data.profile_path}`
            : "static/no_photo_image.jpg";
          var biography = data.biography || "No biography available";
          var shortBio =
            biography.length > 100
              ? biography.substring(0, 100) + "..."
              : biography;
          const fullCredits = data.movie_credits
            .map(
              (credit) => `<dd>${credit.title} (${credit.release_year})</dd>`
            )
            .join("");
          $(element).data("fullCredits", fullCredits);

          // Display initial subset of credits
          const maxDisplayCredits = 5; // Number of movie credits to show initially
          let displayedCredits = data.movie_credits
            .slice(0, maxDisplayCredits)
            .map(
              (credit) => `<dd>${credit.title} (${credit.release_year})</dd>`
            )
            .join("");

          let creditsHtml = `<dl><dt>Movie Credits:</dt>${displayedCredits}</dl>`;
          if (data.movie_credits.length > maxDisplayCredits) {
            creditsHtml += `<dd><span id="more-credits" class="more-link">... More</span></dd>`;
          }

          var imageTag = `<img src="${imagePath}" alt="${data.name} Photo" class="img-fluid" style="width: 185px; height: 278px;">`;

          var buttonsHtml = `
              <div style="text-align: right; padding-top: 10px; display: flex; justify-content: flex-end;">
                <button type="button" class="btn popover-button">Ask MovieBot</button>
                <button type="button" class="btn popover-button" style="margin-left: 5px;">IMDb</button>
                <button type="button" class="btn popover-button" style="margin-left: 5px;">Wiki</button>
                
              </div>`;

          var contentHtml = `
          <div class="movie-title">${data.name}</div>
          <div class="movie-details-card">
            <div class="movie-poster">${imageTag}</div>
            <div class="movie-info">
              <p><em>Birthday:</em> ${data.birthday || "N/A"}</p>
              <p>${creditsHtml}<p>
              <p><em>Biography:</em> <span id="short-bio">${shortBio}</span>
              ${
                biography.length > 100
                  ? `<span id="more-bio" class="more-link">More</span>`
                  : ""
              }
              <div style="display: flex;">
                ${buttonsHtml}

              </div>
            </div>
            
          </div>`;

          $(element).data("fullBiography", data.biography);
          $(element).data("bs.popover").config.content = contentHtml;
          $(element).popover("show");
        })
        .catch((error) => {
          console.error("Error:", error);
          $(element).data("bs.popover").config.content =
            "Details not available";
          $(element).popover("show");
        });
    });

  // Function to hide popover on mouseleave
  function hidePopover() {
    if (!isMouseOverPopover) {
      $(element).popover("hide");
    }
  }

  // Event binding for mouseleave on the triggering element
  $(element)
    .off("mouseleave")
    .on("mouseleave", function () {
      popoverTimeout = setTimeout(hidePopover, 350);
    });

  // Event binding for popover shown event
  $(element)
    .off("mouseleave")
    .on("mouseleave", function () {
      popoverTimeout = setTimeout(hidePopover, 350);
    });

  // Event binding for popover shown event
  $(element)
    .off("shown.bs.popover")
    .on("shown.bs.popover", function () {
      var popoverId = $(element).attr("aria-describedby");
      var $popover = $("#" + popoverId);

      $popover
        .on("mouseenter", function () {
          isMouseOverPopover = true;
          clearTimeout(popoverTimeout);
        })
        .on("mouseleave", function () {
          isMouseOverPopover = false;
          popoverTimeout = setTimeout(hidePopover, 350);
        });

      $popover.find("#more-bio").on("click", function () {
        var fullBiography = $(element).data("fullBiography");
        $popover.find("#short-bio").text(fullBiography);
        $(this).remove(); // Remove the 'More' button
      });

      $popover.find("#more-credits").on("click", function () {
        var fullCreditsHtml = `${$(element).data("fullCredits")}</dl>`;
        $(this).parent().replaceWith(fullCreditsHtml); // Replace the dd with full credits
        $(this).remove(); // Remove the 'More' link
      });

      $popover.find(".chat-btn").on("click", function () {
        var title = $(this).data("title");
        sendPredefinedMessage(`Tell me more about ${title}.`);
      });

      // Here's the binding for the 'More' button
      $popover
        .find("#more-bio")
        .off("click")
        .on("click", function () {
          var fullBiography = $(element).data("fullBiography");
          $popover.find("#short-bio").text(fullBiography);
          $(this).remove(); // Remove the 'More' button after it's clicked
        });
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
