# SymPy Bot

This is a GitHub bot for SymPy. It runs on Render and uses the
[@sympy-bot](https://github.com/sympy-bot) GitHub user.

The bot makes sure that every pull request to SymPy has a release notes entry
in the pull request description. It then automatically adds these notes to the
[release notes](https://github.com/sympy/sympy/wiki/Release-Notes) on the wiki
when the pull request is merged.

See [the guide on the SymPy
wiki](https://github.com/sympy/sympy/wiki/Writing-Release-Notes) on how to
write release notes.

The bot may also do other things in the future. If you have any suggestions or
have found any bugs, please open an
[issue](https://github.com/sympy/sympy-bot/issues). Pull requests are welcome
too.

## Setting up the bot

[This tutorial](https://github-bot-tutorial.readthedocs.io/en/latest) is very
good on how to set up Heroku and write GitHub bots. This bot is based on it,
although it uses Render instead of Heroku.

The bot is tied to Render, so any push to this repo is automatically deployed
there. The Redner
dashboard is at https://dashboard.render.com/

If the bot stops working, look at the logs on the Render dashboard.

Next, you need to set up the bot on GitHub. To do so, follow these steps:

1. Go to the webhooks settings (for instance, at
   https://github.com/sympy/sympy/settings/hooks), and create a new webhook.

   - Set the payload URL to the Render app URL (for instance,
     https://sympy-bot.onrender.com/)
   - Set the content type to `application/json`
   - Generate a random password for the secret. I used the keychain app on my
     Mac to generate a 20 character password with random characters. Save this
     secret, as you will need to enter it in Render as well.
   - Under "Which events would you like to trigger this webhook?" select "Let
     me select individual events.". Then make sure only **Pull requests** is
     checked.
   - Make sure **Active** is checked

2. Go to the Render dashboard and click on "Environment" on the left side.
   Create two config variables:

   - `GH_SECRET`: set this to the secret you created in step 1 above
   - `GH_AUTH`: set this to the personal access token for the `sympy-bot`
     user. If you don't have this or need to regenerate it, login as the bot
     user and go to the personal access token settings (at
     https://github.com/settings/tokens), and create a new token. **VERY
     IMPORTANT:** Give the token `public_repo` access only.

3. Give the `sympy-bot` user push access to the repo. This is required for the
   bot to set commit statuses and to push to the wiki. If you know how to
   allow it to do this without giving it as much access, please let me know. I
   have tried playing with using reviews instead of statuses, but I couldn't
   get it to work.


## Testing

To test, push to a separate branch (`master` has branch protection) on this
repo (you can also set up a separate testing deploy for your fork if you
want). Then go to the Render dashboard and manually deploy the branch. We may
at some point enable automatic deployments for PRs in Render.

### Debugging Webhooks

To debug webhooks, you can go to the webhooks settings for the repo the bot is
set up on (e.g., https://github.com/sympy/sympy/settings/hooks), and click the
webhook for https://sympy-bot.onrender.com/. This will show you all recent
webhooks that were delivered, with the exact JSON that was delivered as well
as the headers and the response. Each webhook has a corresponding UUID (the
delivery id), which is printed by the bot in the logs when it receives it.

## Rate Limits

GitHub has a rate limit of 5000 requests per hour. A single bot action may
result in multiple API requests. You can see the current rate limit and when
it resets at https://sympy-bot.onrender.com/. If the bot detects that its
rate limits are getting very low, it will post a warning comment on a pull
request. Right now, the bot doesn't use the API very much, so we never get
near the rate limits, unless someone were to attempt to spam it. However, in
the future, this could become an issue if the bot is made to do more stuff.
