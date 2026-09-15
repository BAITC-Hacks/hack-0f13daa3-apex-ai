document.addEventListener('DOMContentLoaded', () => {
    const lectureText = document.getElementById('lectureText');
    const generateBtn = document.getElementById('generateBtn');
    const loading = document.getElementById('loading');
    const errorMessage = document.getElementById('errorMessage');
    const resultsSection = document.getElementById('results');
    
    // Tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));
            
            // Add active class to current
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.remove('hidden');
        });
    });

    // Generate Button Click
    generateBtn.addEventListener('click', async () => {
        const text = lectureText.value.trim();
        
        if (!text) {
            showError('Пожалуйста, вставьте текст лекции перед отправкой.');
            return;
        }

        // Reset UI
        hideError();
        resultsSection.classList.add('hidden');
        loading.classList.remove('hidden');
        generateBtn.disabled = true;

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Произошла ошибка при обработке на сервере.');
            }

            const data = await response.json();
            displayResults(data);
            
            // Show results section
            resultsSection.classList.remove('hidden');
            
            // Scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            showError(error.message);
        } finally {
            loading.classList.add('hidden');
            generateBtn.disabled = false;
        }
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function hideError() {
        errorMessage.classList.add('hidden');
    }

    function displayResults(data) {
        // Summary
        document.getElementById('summaryContent').textContent = data.summary || 'Информация отсутствует.';

        // Key points
        const keysList = document.getElementById('keysContent');
        keysList.innerHTML = '';
        if (data.key_points && data.key_points.length > 0) {
            data.key_points.forEach(point => {
                const li = document.createElement('li');
                li.textContent = point;
                keysList.appendChild(li);
            });
        } else {
            keysList.innerHTML = '<li>Информация отсутствует.</li>';
        }

        // Quiz
        const quizContainer = document.getElementById('quizContent');
        quizContainer.innerHTML = '';
        if (data.quiz && data.quiz.length > 0) {
            data.quiz.forEach((q, index) => {
                const item = document.createElement('div');
                item.className = 'quiz-item';
                
                let optionsHtml = '';
                if (q.options) {
                    q.options.forEach(opt => {
                        optionsHtml += `<li>${opt}</li>`;
                    });
                }

                item.innerHTML = `
                    <div class="quiz-question">${index + 1}. ${q.question}</div>
                    <ul class="quiz-options">${optionsHtml}</ul>
                    <div class="quiz-answer">
                        <strong>Правильный ответ:</strong> ${q.correct_answer}<br>
                        <small><em>Источник: ${q.source || 'Не указан'}</em></small>
                    </div>
                `;
                quizContainer.appendChild(item);
            });
        } else {
            quizContainer.innerHTML = 'Нет доступных вопросов.';
        }

        // Flashcards
        const cardsContainer = document.getElementById('flashcardsContent');
        cardsContainer.innerHTML = '';
        if (data.flashcards && data.flashcards.length > 0) {
            data.flashcards.forEach(card => {
                const item = document.createElement('div');
                item.className = 'flashcard';
                item.innerHTML = `
                    <div class="card-inner">
                        <div class="card-question">${card.question}</div>
                        <div class="card-answer">${card.answer}</div>
                    </div>
                `;
                
                // Toggle answer on click
                item.addEventListener('click', () => {
                    const answer = item.querySelector('.card-answer');
                    if (answer.style.display === 'block') {
                        answer.style.display = 'none';
                    } else {
                        answer.style.display = 'block';
                    }
                });

                cardsContainer.appendChild(item);
            });
        } else {
            cardsContainer.innerHTML = 'Нет доступных карточек.';
        }
    }
});
