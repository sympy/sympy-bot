# SymPy Bot

This is a GitHub bot for SymPy. It is run by the
[@sympy-bot](https://github.com/sympy-bot) user on Heroku.

# Setting up the bot

[This tutorial](https://github-bot-tutorial.readthedocs.io/en/latest) is very
good on how to set up Heroku and write GitHub bots. This bot is based on it.

The bot is tied to Heroku, so any push to this repo is automatically deployed
there (it is currently configured to not deploy until the
[Travis](https://travis-ci.org/sympy/sympy-bot) tests pass). The Heroku
dashboard is at https://dashboard.heroku.com/apps/sympy-bot

If the bot stops working, look at the logs with

    heroku logs -a sympy-bot

(you need to install the `heroku` command line tools and have access to the
sympy-bot Heroku app). You can also see the logs on
[Heroku](https://dashboard.heroku.com/apps/sympy-bot/logs).

Next you need to set up the bot on GitHub. To do so, follow these steps:

1. Go to the webhooks settings (for instance, at
  https://github.com/sympy/sympy/settings/hooks), and create a new webhook.

  - Set the payload URL to the Heroku app url (for instance,
    https://sympy-bot.herokuapp.com/)
  - Set the content type to `application/json`
  - Generate a random password for the secret. I used the keychain app on my
    Mac to generate a 20 character password with random characters. Save this
    secret, as you will need to enter it in Heroku as well.
  - Under "Which events would you like to trigger this webhook?" select "Let
    me select individual events.". Then make sure only **Pull requests** is
    checked.
  - Make sure **Active** is checked

2. Go to Heroku and under the settings UI (e.g.,
   https://dashboard.heroku.com/apps/sympy-bot/settings), create two config
   variables:

   - `GH_SECRET`: set this to the secret you created in step 1 above
   - `GH_AUTH`: set this to the personal access token for the `sympy-bot`
     user. If you don't have this or need to regenerate it, login as the bot
     user and go to the personal access token settings (for instance, at
     https://github.com/settings/tokens), and create a new token. **VERY
     IMPORTANT:** Give the token `public_repo` access only.

3. Give the `sympy-bot` user push access to the repo. This is required for the
   bot to set commit statuses and to push to the wiki. If you know how to
   allow it to do this without giving it as much access, please let me know. I
   have tried playing with using reviews instead of statuses, but I couldn't
   get it to work.

Run

    heroku labs:enable runtime-dyno-metadata -a sympy-bot

to enable the bot version environment variable (run this if the version is
"version not found!").

## Testing

There is a testing deploy set up at
https://dashboard.heroku.com/apps/sympy-bot-testing. Currently it is
configured to run on https://github.com/asmeurer/GitHub-Issues-Test.
