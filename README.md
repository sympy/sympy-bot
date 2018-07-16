# SymPy Bot

This is a GitHub bot for SymPy. It is run by the
[@sympy-bot](https://github.com/sympy-bot) user on Heroku.

# Setting up the bot

[This
tutorial](https://github-bot-tutorial.readthedocs.io/en/latest/gidgethub-for-webhooks.html)
is very good on how to set up Heroku and write GitHub bots. This bot is based
on it.

The bot is tied to Heroku, so any push to this repo is automatically deployed
there. The Heroky dashboard is at https://dashboard.heroku.com/apps/sympy-bot

If the bot stops working, look at the logs with

    heroku logs -a sympy-bot

(you need to install the `heroku` command line tools and have access to the
sympy-bot Heroku app). You can also see the logs on
[Heroku](https://dashboard.heroku.com/apps/sympy-bot/logs).
