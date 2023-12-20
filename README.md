# moviechat-bot
So this is a discord bot that you use to talk to GPT-3.5. Whenever the bot mentions a movie, it adds a reaction to the message that mentions that movie. You can click that reaction to add the movie to radarr.

You must setup a discord bot with the correct permissions and get it's token.

The webui allows you to enter the necessary API keys for OpenAI, Radarr and TMDB as well as the URL for Radarr and the Discord token. You should just have to do this once. Google or ChatGPT can tell you how to get the API keys. The OpenAI api key does cost money, but the model we are using is pretty cheap. I'll add functionality to allow you to pick a model as soon as I can.

### Once it is running, you can use talk to the bot in the server you added it to  like this "!! Here is my message" There must be a space after the second !


### How ChatGPT Recommends You Set Up Your Discord Bot for Use with Our Docker Container - 

#### Step 1: Create Your Discord Bot
1. **Create a Discord Account:** Sign up at [Discord's website](https://discord.com/).
2. **Access the Developer Portal:** Log into your Discord account and visit the [Discord Developer Portal](https://discord.com/developers/applications).
3. **Create a New Application:** Click “New Application” in the top right corner. Name your application and click "Create".

#### Step 2: Add a Bot to Your Application
1. In your new application, click on the “Bot” tab.
2. Click “Add Bot” and confirm.
3. Customize your bot:
   - **Username:** Change if desired.
   - **Icon:** Optionally, upload an avatar.
   - **Public Bot:** Generally, leave enabled.
   - **Requires OAuth2 Code Grant:** Keep disabled.

#### Step 3: Secure Your Bot Token
1. Under “Token”, click “Copy” to copy your bot token. Keep this token confidential.
2. You will need to enter this token into our Docker container's web UI later.

#### Step 4: Set Up Bot Permissions
1. Go to the “OAuth2” tab.
2. Under “Scopes”, check “bot”.
3. Under “Bot Permissions”, select the following permissions:
   - Send Messages
   - Send Messages in Threads
   - Add Reactions
   - Read Message History
4. Copy the generated URL at the bottom of the “Scopes” section.

#### Step 5: Invite Your Bot to Your Server
1. Open the copied URL in a web browser.
2. Choose the server to add your bot to (you need 'Manage Server' permissions).
3. Click “Authorize” and complete any CAPTCHA, if prompted.

#### Step 6: Configuring Your Docker Container
1. With our Docker container running, navigate to the provided web UI which should be http://localhost:1138 or http://IP_OF_WHERE_CONAINER_IS_RUNNING:1138
2. Enter the bot token, the Radarr URL and the other required API keys (TMDB, Radarr, OpenAI) into the appropriate fields.
3. Save your settings to start your bot. It should now be operational in your Discord server.

### Important Reminders
- Protect your bot token as well as your API keys. If they gets compromised, you can delete and regenerate any of them.
- The permissions listed are necessary for the bot's functionality. Adjust them according to your needs.
- Ensure you're logged into Discord with a suitable account to add the bot to your desired server.

That's it! You should now have your bot running in your server, fully integrated with our Dockerized application. If you have any questions or need further assistance, feel free to reach out.
