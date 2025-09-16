from flask import Flask, request, render_template, jsonify, redirect, url_for, flash, session
import requests
import sqlite3
import os
import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_' + str(uuid.uuid4()))
DATABASE = "books.db"

# Initialize the Database
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            genre TEXT,
            description TEXT,
            image_url TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'To Read')''')
    conn.commit()
    conn.close()
    
# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
        
# Add book from Google Books API
# You can get a Google Books API key from https://developers.google.com/books/docs/v1/using
GOOGLE_BOOKS_API_KEY = ''

def get_book_data(title):
    url = f'https://www.googleapis.com/books/v1/volumes?q=intitle:{title}'
    # Add API key if provided
    if GOOGLE_BOOKS_API_KEY:
        url += f'&key={GOOGLE_BOOKS_API_KEY}'
        
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            volume_info = data['items'][0]['volumeInfo']
            title = volume_info.get('title', 'N/A')
            author = ', '.join(volume_info.get('authors', ['Unknown']))
            genre = ', '.join(volume_info.get('categories', ['Unknown']))
            description = volume_info.get('description', 'No description available')
            
            # Get image URL if available
            image_url = None
            if 'imageLinks' in volume_info:
                image_url = volume_info['imageLinks'].get('thumbnail')
            
            book_data = {
                'title': title,
                'author': author,
                'genre': genre,
                'description': description,
                'image_url': image_url,
                'date_added': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'To Read'
            }
            return book_data
    return None

# Database operations
def add_book_to_db(book_data):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO books (title, author, genre, description, image_url, date_added, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        book_data['title'], 
        book_data['author'], 
        book_data['genre'], 
        book_data['description'],
        book_data.get('image_url'),
        book_data.get('date_added'),
        book_data.get('status', 'To Read')
    ))
    conn.commit()
    book_id = c.lastrowid
    conn.close()
    return book_id

def get_all_books():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM books ORDER BY date_added DESC")
    books = [dict(row) for row in c.fetchall()]
    conn.close()
    return books

def get_book_by_id(book_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = c.fetchone()
    conn.close()
    if book:
        return dict(book)
    return None

def update_book_status(book_id, status):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE books SET status = ? WHERE id = ?", (status, book_id))
    conn.commit()
    conn.close()
    return True

def delete_book(book_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return True

# Routes
@app.route('/')
def index():
    books = get_all_books()
    return render_template('index.html', books=books)

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    book_data = get_book_data(title)
    if not book_data:
        return jsonify({'error': 'Book not found'}), 404
    
    book_id = add_book_to_db(book_data)
    return jsonify({'success': True, 'book': book_data, 'id': book_id})

@app.route('/update_status/<int:book_id>', methods=['POST'])
def update_status(book_id):
    status = request.form.get('status')
    if not status:
        return jsonify({'error': 'Status is required'}), 400
    
    success = update_book_status(book_id, status)
    if success:
        return redirect(url_for('index'))
    return jsonify({'error': 'Failed to update book status'}), 500

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def remove_book(book_id):
    success = delete_book(book_id)
    if success:
        return redirect(url_for('index'))
    return jsonify({'error': 'Failed to delete book'}), 500

@app.route('/book/<int:book_id>')
def book_details(book_id):
    book = get_book_by_id(book_id)
    if not book:
        return redirect(url_for('index'))
    return render_template('book_details.html', book=book)

@app.route('/suggest_books', methods=['GET'])
def suggest_books():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    url = f'https://www.googleapis.com/books/v1/volumes?q=intitle:{query}&maxResults=5'
    if GOOGLE_BOOKS_API_KEY:
        url += f'&key={GOOGLE_BOOKS_API_KEY}'
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            suggestions = []
            if 'items' in data:
                for item in data['items']:
                    volume_info = item['volumeInfo']
                    title = volume_info.get('title', '')
                    authors = volume_info.get('authors', ['Unknown'])
                    thumbnail = volume_info.get('imageLinks', {}).get('thumbnail', '')
                    suggestions.append({
                        'title': title,
                        'author': ', '.join(authors),
                        'thumbnail': thumbnail
                    })
            return jsonify(suggestions)
    except Exception as e:
        print(f"Error fetching suggestions: {e}")
    return jsonify([])

# Initialize database when the app starts
# Using with_app_context for newer Flask versions
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)