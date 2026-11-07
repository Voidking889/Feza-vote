# 🗳️ Feza School Voting System

A modern, responsive, and dynamic web-based voting system for school elections built with HTML, CSS, JavaScript, and Python (Flask).

## ✨ Features

- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Dynamic Interface**: Real-time updates, smooth animations, and interactive UI
- **Live Results**: Automatic refresh of voting results every 5 seconds
- **Vote Tracking**: Prevents duplicate votes using Student ID
- **Modern UI**: Beautiful gradient design with smooth transitions and animations
- **User-Friendly**: Intuitive interface with clear visual feedback

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python Package Manager)

### Installation

1. **Create a Virtual Environment (Recommended)**
   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the Server**
   ```bash
   python app.py
   ```

5. **Access the Application**
   - Open your browser and navigate to: `http://localhost:3000`

## 📁 Project Structure

```
feza-vote/
├── app.py             # Python/Flask backend server
├── requirements.txt   # Python dependencies
├── public/            # Frontend files
│   ├── index.html     # Main HTML file
│   ├── styles.css     # Responsive CSS styles
│   └── script.js      # Dynamic JavaScript functionality
└── README.md          # Project documentation
```

## 🎯 How to Use

1. **Enter Student ID**: Type your student ID in the input field and click "Check Status"
2. **Select Candidate**: Click on your preferred candidate card
3. **Submit Vote**: Your vote will be automatically submitted
4. **View Results**: See live results in the results section (updates every 5 seconds)

## 🛠️ API Endpoints

- `GET /api/candidates` - Get all candidates
- `POST /api/vote` - Submit a vote
- `GET /api/results` - Get voting results
- `GET /api/check-vote/:voterId` - Check if a voter has already voted
- `POST /api/reset` - Reset all votes (admin function)

## 🎨 Features Breakdown

### Responsive Design
- Mobile-first approach
- Flexible grid layouts
- Adaptive typography
- Touch-friendly buttons

### Dynamic Interface
- Real-time vote updates
- Smooth animations and transitions
- Interactive candidate cards
- Live result bars with percentages
- Modal confirmations

## 🔒 Security Notes

⚠️ **Important**: This is a demo application. For production use, you should:

- Add proper authentication
- Use a real database (MongoDB, PostgreSQL, etc.)
- Implement secure session management
- Add rate limiting
- Use HTTPS
- Add input validation and sanitization
- Implement proper admin authentication for reset function

## 📱 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## 🎓 Customization

### Adding Candidates

Edit the `candidates` list in `app.py`:

```python
candidates = [
    {"id": 1, "name": "Your Name", "position": "Position", "votes": 0, "image": "👤"},
    # Add more candidates...
]
```

### Styling

Modify `public/styles.css` to customize:
- Colors (CSS variables in `:root`)
- Fonts
- Spacing
- Animations

## 📝 License

ISC

## 👥 Contributing

Feel free to submit issues and enhancement requests!

---

Made by Baraka & Ashley 
