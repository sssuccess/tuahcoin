import discord
from discord.ext import commands, tasks
import random
import time
import json

# Bot setup
TOKEN = "token here"
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.members = True  # Enable member intent (if needed)

bot = commands.Bot(command_prefix="!", intents=intents)

# In-memory economy storage
coins = {}
user_inventory = {}  # Store users' items
MOD_ROLE_ID = 1327306991034568745  # Role ID for admins who can give/take coins
FILE_PATH = "path"  # Adjust as needed

# Tuah Empire Items and Their Costs (with lore descriptions)
items = {
    "tuah_sword": {
        "name": "Tuah Sword",
        "price": 500,
        "description": "A legendary sword said to be imbued with the spirit of the Tuah Empire’s ancient warriors."
    },
    "golden_hawk_amulet": {
        "name": "Golden Hawk Amulet",
        "price": 300,
        "description": "A powerful talisman that gives the wearer the strength of a hawk."
    },
    "tuah_shield": {
        "name": "Tuah Shield",
        "price": 400,
        "description": "A shield passed down through generations, symbolizing the empire’s strength and protection."
    },
    "tuah_potion": {
        "name": "Tuah Potion",
        "price": 150,
        "description": "A magical elixir that boosts one’s strength and vitality."
    },
    "tuah_scroll": {
        "name": "Tuah Scroll",
        "price": 200,
        "description": "A scroll filled with ancient wisdom from the empire's founding fathers."
    },
    "hawks_feather": {
        "name": "Hawk’s Feather",
        "price": 100,
        "description": "A mystical feather known to bring good luck and fortune."
    }
}

# Function to save data to file
def save_data():
    with open(FILE_PATH, "w") as f:
        json.dump({"coins": coins, "user_inventory": user_inventory}, f)

# Function to load data from file
def load_data():
    try:
        with open(FILE_PATH, "r") as f:
            data = json.load(f)
            return data.get("coins", {}), data.get("user_inventory", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}, {}

# Load data on bot startup
coins, user_inventory = load_data()

# Function to get user balance
def get_balance(user_id):
    return coins.get(user_id, 0)

# Command: Check balance
@bot.command()
async def balance(ctx):
    user_id = ctx.author.id
    bal = get_balance(user_id)
    await ctx.send(f"{ctx.author.display_name}, you have **{bal}** Tuah Coins!")

# Command: Earn Tuah Coins randomly with delay (10s unless mod)
last_earn_time = {}

@bot.command()
async def earn(ctx):
    user_id = ctx.author.id

    # Check if the user has the mod role
    if MOD_ROLE_ID in [role.id for role in ctx.author.roles]:
        await ctx.send(f"{ctx.author.display_name}, you have no cooldown for earning Tuah Coins!")
    else:
        # Check if the user used earn within the last 10 seconds
        current_time = time.time()
        if user_id in last_earn_time and current_time - last_earn_time[user_id] < 10:
            await ctx.send(f"{ctx.author.display_name}, please wait 10 seconds before earning more Tuah Coins!")
            return
        last_earn_time[user_id] = current_time

    # Earn coins
    amount = random.randint(10, 50)
    coins[user_id] = get_balance(user_id) + amount
    save_data()
    await ctx.send(f"{ctx.author.display_name} earned **{amount}** Tuah Coins! New balance: {coins[user_id]}")

# Command: Gamble coins
@bot.command()
async def gamble(ctx, amount: int):
    user_id = ctx.author.id
    if amount <= 0:
        await ctx.send("Invalid amount! Bet at least 1 Tuah Coin.")
        return
    if get_balance(user_id) < amount:
        await ctx.send("You don't have enough Tuah Coins!")
        return
    
    if random.choice([True, False]):
        coins[user_id] += amount
        await ctx.send(f"🎉 {ctx.author.display_name} won **{amount}** Tuah Coins! New balance: {coins[user_id]}")
    else:
        coins[user_id] -= amount
        await ctx.send(f"💀 {ctx.author.display_name} lost **{amount}** Tuah Coins! New balance: {coins[user_id]}")

# Command: Shop
@bot.command()
async def shop(ctx):
    shop_text = "🛒 **Tuah Empire Item Shop** 🛒\n"
    for item_key, item in items.items():
        shop_text += f"{item['name']} - {item['price']} Tuah Coins\n"
        shop_text += f"  *{item['description']}*\n\n"
    await ctx.send(shop_text)

# Command: Buy items
@bot.command()
async def buy(ctx, item_name: str):
    user_id = ctx.author.id
    item = items.get(item_name)

    if not item:
        await ctx.send("This item doesn't exist in the Tuah Empire shop!")
        return

    cost = item["price"]
    if get_balance(user_id) < cost:
        await ctx.send(f"You don't have enough Tuah Coins to buy the **{item['name']}**! You need {cost} Tuah Coins.")
        return

    # Deduct coins and give item to the user
    coins[user_id] -= cost
    user_items = user_inventory.get(user_id, [])
    user_items.append(item_name)  # Add the item to their inventory
    user_inventory[user_id] = user_items
    save_data()  # Save updated data

    await ctx.send(f"{ctx.author.display_name} bought the **{item['name']}** for **{cost}** Tuah Coins!\n{item['description']}")

# Command: View user inventory
@bot.command()
async def inventory(ctx):
    user_id = ctx.author.id
    user_items = user_inventory.get(user_id, [])
    if not user_items:
        await ctx.send(f"{ctx.author.display_name}, your inventory is empty!")
        return
    inventory_text = f"**{ctx.author.display_name}'s Inventory**:\n"
    for item in user_items:
        inventory_text += f"- {items[item]['name']} - {items[item]['description']}\n"
    await ctx.send(inventory_text)

# Command: Leaderboard
@bot.command()
async def leaderboard(ctx):
    if not coins:
        await ctx.send("No one has earned Tuah Coins yet!")
        return
    
    sorted_users = sorted(coins.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "\n".join([f"{bot.get_user(user).display_name}: **{bal}** Tuah Coins" for user, bal in sorted_users[:10] if bot.get_user(user)])
    await ctx.send(f"🏆 **Tuah Empire Leaderboard** 🏆\n{leaderboard_text}")

# Command: Give coins (Admin only)
@bot.command()
async def give(ctx, amount: int, user_id: int):
    if MOD_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("You don't have permission to use this command!")
        return
    
    user = bot.get_user(user_id)
    if not user:
        await ctx.send("Invalid user ID!")
        return
    
    coins[user_id] = get_balance(user_id) + amount
    save_data()
    await ctx.send(f"Gave **{amount}** Tuah Coins to {user.display_name}. New balance: {coins[user_id]}")

# Command: Take coins (Admin only)
@bot.command()
async def take(ctx, amount: int, user_id: int):
    if MOD_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("You don't have permission to use this command!")
        return
    
    user = bot.get_user(user_id)
    if not user:
        await ctx.send("Invalid user ID!")
        return
    
    coins[user_id] = max(0, get_balance(user_id) - amount)
    save_data()
    await ctx.send(f"Took **{amount}** Tuah Coins from {user.display_name}. New balance: {coins[user_id]}")

# Start the bot
bot.run(TOKEN)
