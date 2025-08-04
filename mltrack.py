import click
import os
import hashlib
import shutil
import sqlite3
from datetime import datetime

DB_File="db.sqlite3"
snapShot_Dir=".mltrack/Snapshots"

#SQLite ka Setup
#data base create kiya yaha
def init_db():
    conn=sqlite3.connect(DB_File)
    c=conn.cursor()
    c.execute(''' CREATE TABLE IF NOT EXISTS commits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        hash TEXT,
        message TEXT,
        timestamp TEXT
        )''')
    conn.commit()
    conn.close()
    
#get hash of file(used to check any changess)(hash=unique code hota hai har file ka)
def get_file_hash(file_path):
    with open(file_path,'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()
    
#Save SnapShot of file
def save_snapshot(file_path, hash):
    snapshot_path=os.path.join(snapShot_Dir,hash)
    shutil.copy(file_path,snapshot_path)
    
@click.group()
def cli():
    pass

@cli.command()
def init():
    os.makedirs(snapShot_Dir,exist_ok=True)
    init_db()
    click.echo("MlTrack Project Intialized ~ Dondo Tto-to Dondo Tto-to ~ ")
    
@cli.command()
@click.argument("file")
def add(file):
    if not os.path.exists(file):
        click.echo("File not Found.")
        return
        
    hash=get_file_hash(file)
    save_snapshot(file,hash)
    click.echo(f"File added with hash: {hash}")
    
@cli.command()
@click.argument("file")
@click.option("-m","--message",prompt="commit message")
def commit(file, message):
    if not os.path.exists(file):
        click.secho(f"File '{file}' not found!", fg="red")
        return
    
    # File ka hash nikaalo
    hash = get_file_hash(file)
    snapshot_path = os.path.join(snapShot_Dir, hash)
    
    # Snapshot check aur create
    if not os.path.exists(snapshot_path):
        click.secho(f"⚠ File '{file}' has not been added yet!", fg="yellow")
        click.secho(f"💡 Run: mltrack add {file} before committing.", fg="blue")
        return
    else:
        click.secho(f"Snapshot already exists for '{file}'", fg="green")
    
    # Database me commit entry save karo
    conn = sqlite3.connect(DB_File)
    c = conn.cursor()
    c.execute(
        "INSERT INTO commits(filename, hash, message, timestamp) VALUES (?, ?, ?, ?)",
        (file, hash, message, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    
    click.secho(f"Committed '{file}' with message: {message}", fg="cyan")

@cli.command()
def log():
    conn=sqlite3.connect(DB_File)
    c=conn.cursor()
    c.execute("SELECT id, message, timestamp FROM commits ORDER BY id DESC")
    rows=c.fetchall()
    
    for id,message,ts in rows:
        click.secho(f"Commit ID: {id}",fg="cyan")
        click.secho(f"Message: {message}",fg="white")
        click.secho(f"Time : {ts}",fg="green")
        
    conn.close()
    
@cli.command()
@click.argument("commit_id")
def restore(commit_id):
    conn=sqlite3.connect(DB_File)
    c=conn.cursor()
    c.execute("SELECT filename,hash From commits WHERE id=?",(commit_id,))
    row=c.fetchone()
    if row:
        filename,filehash=row
        backup_path = os.path.join(snapShot_Dir, filehash)

        if os.path.exists(backup_path):
            shutil.copy(backup_path,filename)
            click.secho(f"Restored '{commit_id}' from last commit", fg="green")
        else:
            click.secho(f"Backup version not found",fg="red")
    else:
        click.secho(f"Commit id: '{commit_id}' not found",fg="red")
        
    conn.close()
    
@cli.command()
def status():
    conn=sqlite3.connect(DB_File)
    c=conn.cursor()
    c.execute("SELECT filename, hash FROM commits ORDER BY  id DESC")
    rows=c.fetchall()
    conn.close()
    
    latest_commits={}
    for filename,hash in rows:
        if filename not in latest_commits:
            latest_commits[filename.strip()]=hash #only most recent
            
    current_files =[f for f in os.listdir() if os.path.isfile(f) and not f.startswith(".")]
    printed =set()
    
    for file in current_files:
        file=file.strip()
        if file in printed:
            continue
        printed.add(file)
        
        file_hash =get_file_hash(file)
        if file in latest_commits:
            if file_hash!=latest_commits[file]:
                click.secho(f"Modified {file}",fg="yellow")
            else:
                click.secho(f"unchanged {file}", fg="green")
        else:
            click.secho(f"Untracked {file}",fg="blue")
        
    for file in latest_commits:
        file=file.strip()
        if file not in printed:
            click.secho(f"Deleted (since last commit): {file}",fg="red")
if __name__=="__main__":
    cli()