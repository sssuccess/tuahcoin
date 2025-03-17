import discord
from discord.ext import commands
import random
import json
import asyncio
import os

# Replace the following with your bot token and mod role ID directly if you need
TOKEN = 'bot token'
MOD_ROLE_ID = 1327306991034568745  # Mod role ID

# Role IDs for shop
GOLD_ROLE_ID = 1351310135556837498
DIAMOND_ROLE_ID = 1351310078749179915

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load data from file
def load_data():
    if os.path.exists('data.json'):
        with open('data.json', 'r') as f:
            return json.load(f)
    return {}

# Save data to file
def save_data():
    with open('data.json', 'w') as f:
        json.dump(data, f)

# Ensure user data exists in the data structure
def ensure_user_data(user_id):
    if user_id not in data:
        data[user_id] = {
            "coins": 0,
            "earn_upgrade_level": 0
        }
        save_data()

# Global variables
data = load_data()
earn_cooldowns = {}

# Command: Check Balance
@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    ensure_user_data(user_id)
    await ctx.send(f"{ctx.author.display_name}, you have **{data[user_id]['coins']}** Tuah Coins.")

# Command: Earn Tuah Coins (10-second cooldown unless mod)
@bot.command()
async def earn(ctx):
    user_id = str(ctx.author.id)
    
    ensure_user_data(user_id)  # Ensure the user data is initialized

    # Check if user is on cooldown
    if user_id in earn_cooldowns:
        if (discord.utils.utcnow() - earn_cooldowns[user_id]).total_seconds() < 3:  # Changed to 3 seconds
            await ctx.send("⏳ You must wait 3 seconds before using !earn again!")
            return

    # Calculate earned amount based on upgrade level
    base_amount = random.randint(10, 50)
    upgrade_multiplier = 1 + (data[user_id]["earn_upgrade_level"] * 0.2)  # 20% more per upgrade level
    amount = int(base_amount * upgrade_multiplier)
    
    # Add earned coins
    data[user_id]["coins"] += amount
    save_data()  # Save the updated data

    # Update cooldown for non-mod users
    if MOD_ROLE_ID not in [role.id for role in ctx.author.roles]:
        earn_cooldowns[user_id] = discord.utils.utcnow()

    await ctx.send(f"{ctx.author.display_name} earned **{amount}** Tuah Coins! New balance: {data[user_id]['coins']}")

# Command: Shop (View available upgrades)
@bot.command()
async def shop(ctx):
    user_id = str(ctx.author.id)
    ensure_user_data(user_id)
    
    upgrade_price = 100 * (data[user_id]["earn_upgrade_level"] + 1)  # Price increases with each upgrade
    gold_price = 1000  # Price for gold role
    diamond_price = 10000  # Price for diamond role
    
    shop_message = f"**Shop**:\n1. Upgrade earn rate: {upgrade_price} Tuah Coins\n"
    shop_message += f"2. Gold Role: {gold_price} Tuah Coins\n3. Diamond Role: {diamond_price} Tuah Coins"
    await ctx.send(shop_message)

@bot.command()
async def buy(ctx, item: str):
    user_id = str(ctx.author.id)
    ensure_user_data(user_id)

    if item.lower() == "earn upgrade":
        # Check if user can afford the upgrade
        upgrade_price = 100 * (data[user_id]["earn_upgrade_level"] + 1)
        if data[user_id]["coins"] >= upgrade_price:
            # Deduct the coins and apply the upgrade
            data[user_id]["coins"] -= upgrade_price
            data[user_id]["earn_upgrade_level"] += 1
            save_data()
            await ctx.send(f"{ctx.author.display_name} successfully upgraded earn rate! New level: {data[user_id]['earn_upgrade_level']}")

        else:
            await ctx.send(f"{ctx.author.display_name}, you don't have enough coins to upgrade earn rate! You need **{upgrade_price}** coins.")

    elif item.lower() == "gold":
        # Gold role purchase logic
        role_id = 1351310135556837498  # Gold role ID
        role_price = 1000
        if data[user_id]["coins"] >= role_price:
            # Deduct the coins and give the role
            data[user_id]["coins"] -= role_price
            save_data()
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            await ctx.author.add_roles(role)
            await ctx.send(f"{ctx.author.display_name} successfully purchased the **Gold** role!")
        else:
            await ctx.send(f"{ctx.author.display_name}, you don't have enough coins to purchase the Gold role! You need **{role_price}** coins.")

    elif item.lower() == "diamond":
        # Diamond role purchase logic
        role_id = 1351310078749179915  # Diamond role ID
        role_price = 10000
        if data[user_id]["coins"] >= role_price:
            # Deduct the coins and give the role
            data[user_id]["coins"] -= role_price
            save_data()
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            await ctx.author.add_roles(role)
            await ctx.send(f"{ctx.author.display_name} successfully purchased the **Diamond** role!")
        else:
            await ctx.send(f"{ctx.author.display_name}, you don't have enough coins to purchase the Diamond role! You need **{role_price}** coins.")

    else:
        await ctx.send("Invalid item. Use `!shop` to view available items.")


# Command: Leaderboard (Top 10 users by coins)
@bot.command()
async def leaderboard(ctx):
    sorted_users = sorted(data.items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
    leaderboard_message = "**Leaderboard (Top 10)**:\n"
    for i, (user_id, user_data) in enumerate(sorted_users, 1):
        user = await bot.fetch_user(user_id)
        leaderboard_message += f"{i}. {user.display_name}: **{user_data['coins']}** Tuah Coins\n"
    await ctx.send(leaderboard_message)

# Command: Gamble (Chance to win coins)
@bot.command()
async def gamble(ctx, amount: int):
    user_id = str(ctx.author.id)
    ensure_user_data(user_id)
    
    if amount <= 0:
        await ctx.send("You must gamble a positive amount of coins.")
        return

    if amount > data[user_id]["coins"]:
        await ctx.send(f"You don't have enough coins to gamble. You only have **{data[user_id]['coins']}** coins.")
        return

    # Determine gamble outcome
    outcome = random.randint(1, 100)
    if outcome <= 50:  # 50% chance to win
        win_amount = amount * 2
        data[user_id]["coins"] += win_amount
        save_data()
        await ctx.send(f"{ctx.author.display_name} gambled and won **{win_amount}** Tuah Coins! New balance: {data[user_id]['coins']}")
    else:
        data[user_id]["coins"] -= amount
        save_data()
        await ctx.send(f"{ctx.author.display_name} gambled and lost **{amount}** Tuah Coins. New balance: {data[user_id]['coins']}")

# Run the bot
bot.run(TOKEN)
