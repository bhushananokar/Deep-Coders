# Mentora

Mentora is an AI-powered adaptive learning platform that personalizes educational content based on individual learning styles and needs. The application uses advanced AI to analyze, adapt, and present content in the most effective way for each user.


## Features

### Content Adaptation
- **Learning Style Personalization**: Visual, Auditory, Kinesthetic, and Reading/Writing
- **Special Needs Support**: Accommodations for Dyslexia, Dyscalculia, ADHD, Dysgraphia, and Auditory Processing
- **Text-to-Speech**: Convert any content to spoken audio
- **Content Chunking**: Break down content into manageable pieces

### Content Sources
- **AI-Generated Content**: Create educational content on any topic
- **PDF Extraction**: Upload and process PDF documents
- **Manual Entry**: Paste or type your own content

### AI Visualizations
- **DALL-E Integration**: Generate visual representations of complex concepts
- **Math Visualizations**: Visual aids for mathematical concepts
- **Instruction Visualizations**: Step-by-step visual guides

### Assessment
- **Personalized Quizzes**: Generate quizzes based on content
- **Skill Tracking**: Monitor progress across different skills
- **Automated Feedback**: Get AI-powered suggestions for improvement

### Learning Paths
- **Custom Learning Journeys**: Create personalized learning paths
- **Skill-Based Recommendations**: Get content recommendations based on weak areas
- **Progress Tracking**: Monitor advancement through learning materials

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Stable internet connection (for AI API access)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Deep-Coders.git
cd Deep-Coders
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

4. Run the application:
```bash
streamlit run DYP_Final/app.py
```

## Usage

### First-time Setup
1. Register an account on the welcome page
2. Set up your learning profile with your learning style and any specific needs
3. Navigate to the dashboard to view your personalized recommendations

### Content Adaptation
1. Go to "Adapt Content" in the navigation menu
2. Either generate new content, paste existing content, or upload a PDF
3. Click "Adapt Content" to create personalized versions based on your profile

### Quiz Creation
1. Navigate to the "Quizzes" section
2. Select "Create Quiz" and enter a topic
3. Customize the difficulty and number of questions
4. Generate and take the quiz

### Learning Paths
1. Go to "Learning Paths"
2. Create a new path focused on specific skills
3. Follow the generated steps to improve in your target areas

## API Keys

Mentora requires two API keys to function:

1. **Groq API Key**: Used for content generation and adaptation
   - Sign up at [groq.com](https://groq.com)
   
2. **OpenAI API Key**: Used for DALL-E visualizations
   - Sign up at [openai.com](https://platform.openai.com)

Both keys can be entered directly in the application's sidebar.

## Customization

### Learning Profile
Adjust your learning profile in the settings to fine-tune how content is adapted:

- **Learning Style**: Choose between Visual, Auditory, Kinesthetic, or Reading/Writing
- **Special Needs**: Select any applicable learning accommodations
- **Chunk Size**: Customize the size of content chunks for ADHD accommodation

### Theme
The application uses a dark theme with orange accents. The theme can be modified in the `ui/rendering.py` file.

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: SQLite
- **AI Services**:
  - Groq LLM API for content generation and adaptation
  - OpenAI DALL-E for visualizations
- **Text Processing**: PyMuPDF for PDF extraction

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the need for more accessible and personalized education
- Thanks to all the open-source libraries that made this project possible
