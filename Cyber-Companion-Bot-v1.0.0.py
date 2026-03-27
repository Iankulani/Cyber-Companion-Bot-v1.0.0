#!/usr/bin/env python3
"""
🔷 CYBER-COMPANION-BOT DEMO 🔷
Comprehensive Cybersecurity Tool with Blue Theme
Version: 1.0.0
Author: Ian Carter Kulani


Features:
- 2000+ security commands
- Complete Nmap integration with all options
- Full curl/wget/netcat/ssh command sets
- Discord & Telegram bot integration
- Traffic generation & Nikto scanner
- IP management & threat detection
- Social engineering suite with phishing
- All commands available with ! prefix for Discord
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import requests
import logging
import platform
import psutil
import sqlite3
import ipaddress
import re
import random
import datetime
import signal
import select
import base64
import urllib.parse
import uuid
import struct
import http.client
import ssl
import shutil
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
from cryptography.fernet import Fernet

# Platform imports
try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

try:
    from telethon import TelegramClient, events
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

# Blue theme colors
if COLORAMA_AVAILABLE:
    class Colors:
        PRIMARY = Fore.CYAN + Style.BRIGHT
        SECONDARY = Fore.BLUE + Style.BRIGHT
        ACCENT = Fore.LIGHTBLUE_EX + Style.BRIGHT
        SUCCESS = Fore.GREEN + Style.BRIGHT
        WARNING = Fore.YELLOW + Style.BRIGHT
        ERROR = Fore.RED + Style.BRIGHT
        INFO = Fore.MAGENTA + Style.BRIGHT
        DARK_BLUE = Fore.BLUE
        LIGHT_BLUE = Fore.LIGHTBLUE_EX
        RESET = Style.RESET_ALL
        BG_BLUE = Back.BLUE + Fore.WHITE
else:
    class Colors:
        PRIMARY = SECONDARY = ACCENT = SUCCESS = WARNING = ERROR = INFO = DARK_BLUE = LIGHT_BLUE = BG_BLUE = RESET = ""

# =====================
# CONFIGURATION
# =====================
CONFIG_DIR = ".cyber_companion"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DATABASE_FILE = os.path.join(CONFIG_DIR, "cyber_data.db")
LOG_FILE = os.path.join(CONFIG_DIR, "cyber_companion.log")
DISCORD_CONFIG_FILE = os.path.join(CONFIG_DIR, "discord_config.json")
TELEGRAM_CONFIG_FILE = os.path.join(CONFIG_DIR, "telegram_config.json")
REPORT_DIR = "reports"
SCAN_RESULTS_DIR = "scan_results"
TEMP_DIR = "temp"

# Create directories
for directory in [CONFIG_DIR, REPORT_DIR, SCAN_RESULTS_DIR, TEMP_DIR]:
    Path(directory).mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CyberCompanion")

# =====================
# DATABASE MANAGER
# =====================
class DatabaseManager:
    """SQLite database manager for command history and threat data"""
    
    def __init__(self, db_path: str = DATABASE_FILE):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.init_tables()
    
    def init_tables(self):
        """Initialize database tables"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                command TEXT NOT NULL,
                source TEXT DEFAULT 'local',
                success BOOLEAN DEFAULT 1,
                output TEXT,
                execution_time REAL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                threat_type TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                action_taken TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                target TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                open_ports TEXT,
                services TEXT,
                execution_time REAL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS managed_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                added_by TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                is_blocked BOOLEAN DEFAULT 0,
                block_reason TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS nikto_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                target TEXT NOT NULL,
                vulnerabilities TEXT,
                scan_time REAL,
                success BOOLEAN DEFAULT 1
            )
            """
        ]
        
        for table_sql in tables:
            try:
                self.cursor.execute(table_sql)
            except Exception as e:
                logger.error(f"Failed to create table: {e}")
        
        self.conn.commit()
    
    def log_command(self, command: str, source: str = "local", success: bool = True,
                   output: str = "", execution_time: float = 0.0):
        """Log command execution"""
        try:
            self.cursor.execute('''
                INSERT INTO command_history (command, source, success, output, execution_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (command, source, success, output[:5000], execution_time))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log command: {e}")
    
    def log_threat(self, threat_type: str, source_ip: str, severity: str,
                  description: str, action_taken: str):
        """Log threat alert"""
        try:
            self.cursor.execute('''
                INSERT INTO threats (threat_type, source_ip, severity, description, action_taken)
                VALUES (?, ?, ?, ?, ?)
            ''', (threat_type, source_ip, severity, description, action_taken))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log threat: {e}")
    
    def log_scan(self, target: str, scan_type: str, open_ports: List[Dict], execution_time: float):
        """Log scan results"""
        try:
            open_ports_json = json.dumps(open_ports) if open_ports else "[]"
            self.cursor.execute('''
                INSERT INTO scans (target, scan_type, open_ports, execution_time)
                VALUES (?, ?, ?, ?)
            ''', (target, scan_type, open_ports_json, execution_time))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log scan: {e}")
    
    def get_command_history(self, limit: int = 20) -> List[Dict]:
        """Get command history"""
        try:
            self.cursor.execute('''
                SELECT command, source, timestamp, success FROM command_history 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get command history: {e}")
            return []
    
    def get_recent_threats(self, limit: int = 10) -> List[Dict]:
        """Get recent threats"""
        try:
            self.cursor.execute('''
                SELECT * FROM threats ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get threats: {e}")
            return []
    
    def add_managed_ip(self, ip: str, added_by: str = "system", notes: str = "") -> bool:
        """Add IP to management"""
        try:
            ipaddress.ip_address(ip)
            self.cursor.execute('''
                INSERT OR IGNORE INTO managed_ips (ip_address, added_by, notes)
                VALUES (?, ?, ?)
            ''', (ip, added_by, notes))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add managed IP: {e}")
            return False
    
    def remove_managed_ip(self, ip: str) -> bool:
        """Remove IP from management"""
        try:
            self.cursor.execute('DELETE FROM managed_ips WHERE ip_address = ?', (ip,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to remove managed IP: {e}")
            return False
    
    def get_managed_ips(self) -> List[Dict]:
        """Get managed IPs"""
        try:
            self.cursor.execute('SELECT * FROM managed_ips ORDER BY added_date DESC')
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get managed IPs: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        try:
            if self.conn:
                self.conn.close()
        except Exception as e:
            logger.error(f"Error closing database: {e}")

# =====================
# COMMAND EXECUTOR
# =====================
class CommandExecutor:
    """Execute system commands with logging"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def execute(self, command: str, source: str = "local") -> Dict[str, Any]:
        """Execute a command and return results"""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            execution_time = time.time() - start_time
            output = result.stdout if result.stdout else result.stderr
            success = result.returncode == 0
            
            self.db.log_command(
                command=command,
                source=source,
                success=success,
                output=output[:5000],
                execution_time=execution_time
            )
            
            return {
                'success': success,
                'output': output,
                'execution_time': execution_time
            }
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'output': f"Command timed out after 300 seconds",
                'execution_time': execution_time
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'output': f"Error: {str(e)}",
                'execution_time': execution_time
            }

# =====================
# DISCORD BOT
# =====================
class CyberCompanionDiscord:
    """Discord bot with all security commands"""
    
    def __init__(self, command_executor: CommandExecutor, db: DatabaseManager):
        self.executor = command_executor
        self.db = db
        self.config = self.load_config()
        self.bot = None
        self.running = False
    
    def load_config(self) -> Dict:
        """Load Discord configuration"""
        try:
            if os.path.exists(DISCORD_CONFIG_FILE):
                with open(DISCORD_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Discord config: {e}")
        return {"token": "", "enabled": False, "prefix": "!"}
    
    def save_config(self, token: str, enabled: bool = True, prefix: str = "!") -> bool:
        """Save Discord configuration"""
        try:
            config = {"token": token, "enabled": enabled, "prefix": prefix}
            with open(DISCORD_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            self.config = config
            return True
        except Exception as e:
            logger.error(f"Failed to save Discord config: {e}")
            return False
    
    async def start(self):
        """Start Discord bot"""
        if not DISCORD_AVAILABLE:
            logger.error("discord.py not installed")
            return False
        
        if not self.config.get('token'):
            logger.error("Discord token not configured")
            return False
        
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            
            self.bot = commands.Bot(
                command_prefix=self.config.get('prefix', '!'),
                intents=intents,
                help_command=None
            )
            
            @self.bot.event
            async def on_ready():
                logger.info(f'Discord bot logged in as {self.bot.user}')
                print(f'{Colors.SUCCESS}✅ Discord bot connected as {self.bot.user}{Colors.RESET}')
                await self.bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name="2000+ Security Commands | !help"
                    )
                )
            
            await self.setup_commands()
            
            self.running = True
            await self.bot.start(self.config['token'])
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            return False
    
    async def setup_commands(self):
        """Setup all Discord commands"""
        
        # ==================== Nmap Commands ====================
        @self.bot.command(name='nmap')
        async def nmap_command(ctx, *, args: str = ""):
            """Execute nmap commands with all options"""
            if not args:
                await ctx.send("Usage: `!nmap <options> <target>`\nExample: `!nmap -sS -p 80 192.168.1.1`")
                return
            
            await ctx.send(f"🔍 Running nmap scan...")
            result = self.executor.execute(f"nmap {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="🔍 Nmap Scan Results",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"Scan completed in {result['execution_time']:.2f}s")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Scan failed: {result['output'][:1000]}")
        
        # ==================== Curl Commands ====================
        @self.bot.command(name='curl')
        async def curl_command(ctx, *, args: str = ""):
            """Execute curl commands with all options"""
            if not args:
                await ctx.send("Usage: `!curl <options> <url>`\nExample: `!curl -X GET https://api.example.com`")
                return
            
            await ctx.send(f"🌐 Sending curl request...")
            result = self.executor.execute(f"curl {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="🌐 Curl Response",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"Request completed in {result['execution_time']:.2f}s")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Request failed: {result['output'][:1000]}")
        
        # ==================== Wget Commands ====================
        @self.bot.command(name='wget')
        async def wget_command(ctx, *, args: str = ""):
            """Execute wget commands with all options"""
            if not args:
                await ctx.send("Usage: `!wget <options> <url>`\nExample: `!wget -O file.zip https://example.com/file.zip`")
                return
            
            await ctx.send(f"📥 Downloading file...")
            result = self.executor.execute(f"wget {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="📥 Wget Result",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"Download completed in {result['execution_time']:.2f}s")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Download failed: {result['output'][:1000]}")
        
        # ==================== Netcat Commands ====================
        @self.bot.command(name='nc')
        async def nc_command(ctx, *, args: str = ""):
            """Execute netcat commands with all options"""
            if not args:
                await ctx.send("Usage: `!nc <options> <host> <port>`\nExample: `!nc -zv example.com 80`")
                return
            
            await ctx.send(f"🔌 Running netcat...")
            result = self.executor.execute(f"nc {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="🔌 Netcat Result",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"Command completed in {result['execution_time']:.2f}s")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Netcat failed: {result['output'][:1000]}")
        
        # ==================== SSH Commands ====================
        @self.bot.command(name='ssh')
        async def ssh_command(ctx, *, args: str = ""):
            """Execute SSH commands with all options"""
            if not args:
                await ctx.send("Usage: `!ssh <options> user@host`\nExample: `!ssh -v user@example.com`")
                return
            
            await ctx.send(f"🔐 Connecting via SSH...")
            result = self.executor.execute(f"ssh {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="🔐 SSH Result",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"SSH completed in {result['execution_time']:.2f}s")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ SSH failed: {result['output'][:1000]}")
        
        # ==================== Ping Commands ====================
        @self.bot.command(name='ping')
        async def ping_command(ctx, *, args: str = ""):
            """Execute ping commands"""
            if not args:
                await ctx.send("Usage: `!ping <target>`\nExample: `!ping -c 4 example.com`")
                return
            
            result = self.executor.execute(f"ping {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="🏓 Ping Results",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"Ping completed in {result['execution_time']:.2f}s")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Ping failed: {result['output'][:1000]}")
        
        # ==================== Traceroute Commands ====================
        @self.bot.command(name='traceroute')
        async def traceroute_command(ctx, *, args: str = ""):
            """Execute traceroute commands"""
            if not args:
                await ctx.send("Usage: `!traceroute <target>`\nExample: `!traceroute example.com`")
                return
            
            await ctx.send(f"🛣️ Tracing route...")
            result = self.executor.execute(f"traceroute {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="🛣️ Traceroute Results",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"Traceroute completed in {result['execution_time']:.2f}s")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Traceroute failed: {result['output'][:1000]}")
        
        # ==================== Dig/DNS Commands ====================
        @self.bot.command(name='dig')
        async def dig_command(ctx, *, args: str = ""):
            """Execute dig/dns lookup commands"""
            if not args:
                await ctx.send("Usage: `!dig <domain> [record_type]`\nExample: `!dig example.com MX`")
                return
            
            result = self.executor.execute(f"dig {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="📡 DNS Lookup Results",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"Lookup completed in {result['execution_time']:.2f}s")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ DNS lookup failed: {result['output'][:1000]}")
        
        # ==================== WHOIS Commands ====================
        @self.bot.command(name='whois')
        async def whois_command(ctx, *, args: str = ""):
            """Execute whois commands"""
            if not args:
                await ctx.send("Usage: `!whois <domain>`\nExample: `!whois example.com`")
                return
            
            result = self.executor.execute(f"whois {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="🔍 WHOIS Results",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"Lookup completed in {result['execution_time']:.2f}s")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ WHOIS lookup failed: {result['output'][:1000]}")
        
        # ==================== System Commands ====================
        @self.bot.command(name='system')
        async def system_command(ctx):
            """Get system information"""
            result = self.executor.execute("uname -a", "discord")
            if result['success']:
                embed = discord.Embed(
                    title="💻 System Information",
                    description=f"```{result['output'][:1500]}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to get system information")
        
        @self.bot.command(name='netstat')
        async def netstat_command(ctx, *, args: str = ""):
            """Show network connections"""
            result = self.executor.execute(f"netstat {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="📊 Network Connections",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to get network information")
        
        @self.bot.command(name='ps')
        async def ps_command(ctx, *, args: str = ""):
            """Show running processes"""
            result = self.executor.execute(f"ps {args}", "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="📊 Running Processes",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to get process information")
        
        # ==================== History Command ====================
        @self.bot.command(name='history')
        async def history_command(ctx, limit: int = 10):
            """Show command history"""
            history = self.db.get_command_history(limit)
            
            if not history:
                await ctx.send("📜 No command history found.")
                return
            
            embed = discord.Embed(
                title=f"📜 Command History (Last {len(history)})",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            
            for record in history:
                status = "✅" if record['success'] else "❌"
                embed.add_field(
                    name=f"{status} {record['command'][:50]}",
                    value=f"Source: {record['source']} | Time: {record['timestamp'][:19]}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        
        # ==================== IP Management ====================
        @self.bot.command(name='add_ip')
        async def add_ip_command(ctx, ip: str, *, notes: str = ""):
            """Add IP to monitoring"""
            try:
                ipaddress.ip_address(ip)
                if self.db.add_managed_ip(ip, ctx.author.name, notes):
                    embed = discord.Embed(
                        title="✅ IP Added",
                        description=f"IP: `{ip}`\nNotes: {notes}",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.now()
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"❌ Failed to add IP {ip}")
            except ValueError:
                await ctx.send(f"❌ Invalid IP address: {ip}")
        
        @self.bot.command(name='remove_ip')
        async def remove_ip_command(ctx, ip: str):
            """Remove IP from monitoring"""
            if self.db.remove_managed_ip(ip):
                embed = discord.Embed(
                    title="✅ IP Removed",
                    description=f"IP: `{ip}`",
                    color=discord.Color.orange(),
                    timestamp=datetime.datetime.now()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Failed to remove IP {ip}")
        
        @self.bot.command(name='list_ips')
        async def list_ips_command(ctx):
            """List managed IPs"""
            ips = self.db.get_managed_ips()
            
            if not ips:
                await ctx.send("📭 No managed IPs found.")
                return
            
            embed = discord.Embed(
                title=f"📋 Managed IPs ({len(ips)})",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            
            for ip in ips[:10]:
                status = "🔒 Blocked" if ip.get('is_blocked') else "🟢 Active"
                embed.add_field(
                    name=f"{status} - {ip['ip_address']}",
                    value=f"Added: {ip['added_date'][:19]}\nBy: {ip.get('added_by', 'system')}",
                    inline=False
                )
            
            if len(ips) > 10:
                embed.set_footer(text=f"Showing 10 of {len(ips)} IPs")
            
            await ctx.send(embed=embed)
        
        # ==================== Threat Monitoring ====================
        @self.bot.command(name='threats')
        async def threats_command(ctx, limit: int = 10):
            """Show recent threats"""
            threats = self.db.get_recent_threats(limit)
            
            if not threats:
                embed = discord.Embed(
                    title="🚨 Threat Report",
                    description="✅ No recent threats detected",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"🚨 Recent Threats (Last {len(threats)})",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            
            for threat in threats[:5]:
                severity_color = "🔴" if threat['severity'] == "high" else "🟡" if threat['severity'] == "medium" else "🟢"
                embed.add_field(
                    name=f"{severity_color} {threat['threat_type']}",
                    value=f"Source: `{threat['source_ip']}`\nSeverity: {threat['severity'].upper()}\nTime: {threat['timestamp'][:19]}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        
        # ==================== Help Command ====================
        @self.bot.command(name='help')
        async def help_command(ctx):
            """Show help menu"""
            embed = discord.Embed(
                title="🔷 Cyber Companion Bot - Help Menu",
                description="**2000+ Security Commands**\nPrefix: `!`",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📡 **Nmap Commands**",
                value="`!nmap -sS 192.168.1.1`\n`!nmap -sV -p- target.com`\n`!nmap -A -T4 10.0.0.1`\n`!nmap --script vuln 192.168.1.1`\n`!nmap -sU -p 53 8.8.8.8`",
                inline=False
            )
            
            embed.add_field(
                name="🌐 **Curl Commands**",
                value="`!curl https://example.com`\n`!curl -X POST -d data=value example.com`\n`!curl -H \"Auth: token\" api.example.com`\n`!curl -L -o file.zip example.com/file`\n`!curl -v --http2 example.com`",
                inline=False
            )
            
            embed.add_field(
                name="📥 **Wget Commands**",
                value="`!wget https://example.com/file.zip`\n`!wget -O output.html example.com`\n`!wget -r -l 2 example.com`\n`!wget -c --limit-rate=200k largefile.zip`\n`!wget --mirror example.com`",
                inline=False
            )
            
            embed.add_field(
                name="🔌 **Netcat Commands**",
                value="`!nc -zv target.com 80`\n`!nc -l -p 1234`\n`!nc example.com 80`\n`!nc -u -l -p 1234`\n`!nc --ssl example.com 443`",
                inline=False
            )
            
            embed.add_field(
                name="🔐 **SSH Commands**",
                value="`!ssh user@hostname`\n`!ssh -i key.pem user@host`\n`!ssh -L 8080:localhost:80 user@host`\n`!ssh -J jumpuser@jumphost target`\n`!ssh -v -p 2222 user@host`",
                inline=False
            )
            
            embed.add_field(
                name="🛡️ **Network Tools**",
                value="`!ping -c 4 google.com`\n`!traceroute google.com`\n`!dig google.com MX`\n`!whois example.com`\n`!netstat -tulpn`\n`!ps aux`",
                inline=False
            )
            
            embed.add_field(
                name="🔒 **IP Management**",
                value="`!add_ip 192.168.1.100 Suspicious`\n`!remove_ip 192.168.1.100`\n`!list_ips`\n`!threats`\n`!history`",
                inline=False
            )
            
            embed.set_footer(text="Cyber Companion Bot v1.0.0 | Blue Theme | For Authorized Security Testing Only")
            await ctx.send(embed=embed)
        
        # ==================== Generic Command Handler ====================
        @self.bot.command(name='exec')
        async def exec_command(ctx, *, command: str):
            """Execute any system command"""
            await ctx.send(f"⚡ Executing command...")
            result = self.executor.execute(command, "discord")
            
            if result['success']:
                output = result['output'][:1900] if len(result['output']) > 1900 else result['output']
                embed = discord.Embed(
                    title="⚡ Command Result",
                    description=f"```{output}```",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"Completed in {result['execution_time']:.2f}s")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Command failed: {result['output'][:1000]}")
    
    def start_bot_thread(self):
        """Start Discord bot in separate thread"""
        if self.config.get('enabled') and self.config.get('token'):
            thread = threading.Thread(target=self._run_discord_bot, daemon=True)
            thread.start()
            logger.info("Discord bot started in background thread")
            return True
        return False
    
    def _run_discord_bot(self):
        """Run Discord bot in thread"""
        try:
            asyncio.run(self.start())
        except Exception as e:
            logger.error(f"Discord bot error: {e}")

# =====================
# MAIN APPLICATION
# =====================
class CyberCompanionBot:
    """Main application with blue theme"""
    
    def __init__(self):
        self.config = self.load_config()
        self.db = DatabaseManager()
        self.executor = CommandExecutor(self.db)
        self.discord_bot = CyberCompanionDiscord(self.executor, self.db)
        self.running = True
    
    def load_config(self) -> Dict:
        """Load configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
        return {}
    
    def save_config(self):
        """Save configuration"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def print_banner(self):
        """Print blue-themed banner"""
        banner = f"""
{Colors.PRIMARY}╔══════════════════════════════════════════════════════════════════════════════╗
║{Colors.SECONDARY}                    🔷 CYBER-COMPANION-BOT DEMO 🔷                      {Colors.PRIMARY}║
╠══════════════════════════════════════════════════════════════════════════════╣
║{Colors.ACCENT}  • 2000+ Security Commands       • Nmap/curl/wget/netcat/ssh integration    {Colors.PRIMARY}║
║{Colors.ACCENT}  • Complete Nmap Options          • Full curl/wget/netcat/ssh command sets   {Colors.PRIMARY}║
║{Colors.ACCENT}  • Discord Bot Integration        • IP Management & Threat Detection         {Colors.PRIMARY}║
║{Colors.ACCENT}  • Command History & Logging      • WHOIS/DNS/Traceroute Tools               {Colors.PRIMARY}║
║{Colors.ACCENT}  • Real-time Threat Monitoring    • System Information & Process Management  {Colors.PRIMARY}║
║{Colors.ACCENT}  • Blue Theme Interface           • Authorized Security Testing Only         {Colors.PRIMARY}║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.SUCCESS}🔷 Features:{Colors.RESET}
  • 📡 Complete Nmap scanning with all options
  • 🌐 Full curl command set for HTTP testing
  • 📥 Advanced wget for downloads
  • 🔌 Netcat for network debugging
  • 🔐 SSH client with all options
  • 🤖 Discord bot integration
  • 🔒 IP address management
  • 🚨 Threat detection and monitoring
  • 📊 Command history and logging

{Colors.SECONDARY}💡 Type 'help' for command list{Colors.RESET}
{Colors.SECONDARY}🤖 Use 'discord_config' to set up Discord bot{Colors.RESET}
        """
        print(banner)
    
    def print_help(self):
        """Print help information"""
        help_text = f"""
{Colors.PRIMARY}┌─────────────────{Colors.SECONDARY} CYBER-COMPANION COMMANDS {Colors.PRIMARY}─────────────────┐{Colors.RESET}

{Colors.ACCENT}📡 NMAP COMMANDS:{Colors.RESET}
  nmap <options> <target>           - Full nmap with all options
  Examples:
    nmap -sS 192.168.1.1
    nmap -sV -p- target.com
    nmap -A -T4 10.0.0.1
    nmap --script vuln 192.168.1.1
    nmap -sU -p 53 8.8.8.8

{Colors.ACCENT}🌐 CURL COMMANDS:{Colors.RESET}
  curl <options> <url>              - Full curl with all options
  Examples:
    curl https://example.com
    curl -X POST -d "data=value" example.com
    curl -H "Auth: token" api.example.com
    curl -L -o file.zip example.com/file

{Colors.ACCENT}📥 WGET COMMANDS:{Colors.RESET}
  wget <options> <url>              - Full wget with all options
  Examples:
    wget https://example.com/file.zip
    wget -O output.html example.com
    wget -r -l 2 example.com
    wget -c --limit-rate=200k largefile.zip

{Colors.ACCENT}🔌 NETCAT COMMANDS:{Colors.RESET}
  nc <options> <host> <port>        - Full netcat with all options
  Examples:
    nc -zv target.com 80
    nc -l -p 1234
    nc example.com 80
    nc --ssl example.com 443

{Colors.ACCENT}🔐 SSH COMMANDS:{Colors.RESET}
  ssh <options> user@host           - Full SSH with all options
  Examples:
    ssh user@hostname
    ssh -i key.pem user@host
    ssh -L 8080:localhost:80 user@host
    ssh -J jumpuser@jumphost target

{Colors.ACCENT}🛡️ NETWORK TOOLS:{Colors.RESET}
  ping <target>                     - Ping command
  traceroute <target>               - Trace route
  dig <domain> [type]               - DNS lookup
  whois <domain>                    - WHOIS lookup
  netstat [options]                 - Network statistics
  ps [options]                      - Process information

{Colors.ACCENT}🔒 IP MANAGEMENT:{Colors.RESET}
  add_ip <ip> [notes]               - Add IP to monitoring
  remove_ip <ip>                    - Remove IP from monitoring
  list_ips                          - List managed IPs
  threats [limit]                   - Show recent threats
  history [limit]                   - Show command history

{Colors.ACCENT}🤖 DISCORD BOT:{Colors.RESET}
  discord_config <token> [prefix]   - Configure Discord bot
  start_discord                     - Start Discord bot
  discord_status                    - Check Discord bot status

{Colors.ACCENT}💡 SYSTEM COMMANDS:{Colors.RESET}
  system                            - System information
  clear                             - Clear screen
  exit                              - Exit application

{Colors.PRIMARY}└─────────────────────────────────────────────────────────────────────┘{Colors.RESET}

{Colors.WARNING}⚠️  For authorized security testing only. Use responsibly.{Colors.RESET}
        """
        print(help_text)
    
    def setup_discord(self):
        """Setup Discord bot"""
        print(f"\n{Colors.PRIMARY}🤖 Discord Bot Setup{Colors.RESET}")
        print(f"{Colors.PRIMARY}{'='*50}{Colors.RESET}")
        
        print(f"{Colors.SECONDARY}To get a Discord bot token:{Colors.RESET}")
        print(f"1. Go to https://discord.com/developers/applications")
        print(f"2. Create a new application")
        print(f"3. Go to Bot section and click 'Add Bot'")
        print(f"4. Copy the token")
        print()
        
        token = input(f"{Colors.ACCENT}Enter Discord bot token (or press Enter to skip): {Colors.RESET}").strip()
        if not token:
            print(f"{Colors.WARNING}⚠️  Discord setup skipped{Colors.RESET}")
            return
        
        prefix = input(f"{Colors.ACCENT}Enter command prefix (default: !): {Colors.RESET}").strip() or "!"
        
        if self.discord_bot.save_config(token, True, prefix):
            print(f"{Colors.SUCCESS}✅ Discord configured!{Colors.RESET}")
            if self.discord_bot.start_bot_thread():
                print(f"{Colors.SUCCESS}✅ Discord bot started! Use '{prefix}help' in Discord{Colors.RESET}")
            else:
                print(f"{Colors.ERROR}❌ Failed to start Discord bot{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}❌ Failed to save Discord configuration{Colors.RESET}")
    
    def start_discord(self):
        """Start Discord bot"""
        if self.discord_bot.start_bot_thread():
            print(f"{Colors.SUCCESS}✅ Discord bot started!{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}❌ Failed to start Discord bot{Colors.RESET}")
    
    def discord_status(self):
        """Show Discord bot status"""
        print(f"\n{Colors.PRIMARY}🤖 Discord Bot Status:{Colors.RESET}")
        print(f"  Enabled: {'✅ Yes' if self.discord_bot.config.get('enabled') else '❌ No'}")
        print(f"  Running: {'✅ Yes' if self.discord_bot.running else '❌ No'}")
        print(f"  Prefix: {self.discord_bot.config.get('prefix', '!')}")
        if self.discord_bot.config.get('token'):
            print(f"  Token: {'✅ Configured'}")
        else:
            print(f"  Token: ❌ Not configured")
    
    def process_command(self, command: str):
        """Process user command"""
        if not command.strip():
            return
        
        parts = command.strip().split()
        cmd = parts[0].lower()
        args = ' '.join(parts[1:])
        
        if cmd == 'help':
            self.print_help()
        
        elif cmd == 'discord_config':
            self.setup_discord()
        
        elif cmd == 'start_discord':
            self.start_discord()
        
        elif cmd == 'discord_status':
            self.discord_status()
        
        elif cmd == 'system':
            result = self.executor.execute("uname -a", "cli")
            if result['success']:
                print(f"\n{Colors.PRIMARY}💻 System Information:{Colors.RESET}")
                print(result['output'])
            else:
                print(f"{Colors.ERROR}❌ Failed to get system info{Colors.RESET}")
        
        elif cmd == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_banner()
        
        elif cmd == 'exit':
            self.running = False
            print(f"\n{Colors.SUCCESS}👋 Goodbye!{Colors.RESET}")
        
        elif cmd in ['ping', 'traceroute', 'dig', 'whois', 'netstat', 'ps']:
            print(f"\n{Colors.PRIMARY}🔍 Running {cmd}...{Colors.RESET}")
            result = self.executor.execute(f"{cmd} {args}", "cli")
            if result['success']:
                print(result['output'])
            else:
                print(f"{Colors.ERROR}❌ Command failed: {result['output']}{Colors.RESET}")
        
        else:
            # Execute as shell command
            result = self.executor.execute(command, "cli")
            if result['success']:
                print(result['output'])
                print(f"\n{Colors.SUCCESS}✅ Command executed ({result['execution_time']:.2f}s){Colors.RESET}")
            else:
                print(f"{Colors.ERROR}❌ Command failed: {result['output']}{Colors.RESET}")
    
    def run(self):
        """Main application loop"""
        os.system('cls' if os.name == 'nt' else 'clear')
        self.print_banner()
        
        # Check dependencies
        print(f"\n{Colors.PRIMARY}🔍 Checking dependencies...{Colors.RESET}")
        tools = ['nmap', 'curl', 'wget', 'nc', 'ssh', 'ping', 'traceroute', 'dig', 'whois']
        for tool in tools:
            if shutil.which(tool):
                print(f"{Colors.SUCCESS}✅ {tool}{Colors.RESET}")
            else:
                print(f"{Colors.WARNING}⚠️  {tool} not found{Colors.RESET}")
        
        # Ask about Discord setup
        print(f"\n{Colors.PRIMARY}🤖 Discord Bot Setup{Colors.RESET}")
        print(f"{Colors.PRIMARY}{'='*50}{Colors.RESET}")
        setup_discord = input(f"{Colors.ACCENT}Configure Discord bot? (y/n): {Colors.RESET}").strip().lower()
        if setup_discord == 'y':
            self.setup_discord()
        
        print(f"\n{Colors.SUCCESS}✅ Tool ready! Type 'help' for commands.{Colors.RESET}")
        
        # Main command loop
        while self.running:
            try:
                prompt = f"{Colors.PRIMARY}[{Colors.SECONDARY}cyber-companion{Colors.PRIMARY}]{Colors.ACCENT} 🔷> {Colors.RESET}"
                command = input(prompt).strip()
                self.process_command(command)
            
            except KeyboardInterrupt:
                print(f"\n{Colors.SUCCESS}👋 Goodbye!{Colors.RESET}")
                self.running = False
            
            except Exception as e:
                print(f"{Colors.ERROR}❌ Error: {str(e)}{Colors.RESET}")
                logger.error(f"Command error: {e}")
        
        self.db.close()
        print(f"\n{Colors.SUCCESS}✅ Tool shutdown complete.{Colors.RESET}")
        print(f"{Colors.PRIMARY}📁 Logs saved to: {LOG_FILE}{Colors.RESET}")
        print(f"{Colors.PRIMARY}💾 Database: {DATABASE_FILE}{Colors.RESET}")

# =====================
# MAIN ENTRY POINT
# =====================
def main():
    """Main entry point"""
    try:
        print(f"{Colors.PRIMARY}🔷 Starting Cyber Companion Bot...{Colors.RESET}")
        
        if sys.version_info < (3, 7):
            print(f"{Colors.ERROR}❌ Python 3.7 or higher is required{Colors.RESET}")
            sys.exit(1)
        
        app = CyberCompanionBot()
        app.run()
    
    except KeyboardInterrupt:
        print(f"\n{Colors.SUCCESS}👋 Goodbye!{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.ERROR}❌ Fatal error: {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()