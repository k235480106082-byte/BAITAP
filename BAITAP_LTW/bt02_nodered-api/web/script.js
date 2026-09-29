// Student API Demo - Bài Tập 2 Frontend

document.addEventListener('DOMContentLoaded', function() {
    // Elements - Students
    const btnFetchStudents = document.getElementById('btn-fetch-students');
    const studentsLoading = document.getElementById('students-loading');
    const studentsError = document.getElementById('students-error');
    const studentsData = document.getElementById('students-data');
    const studentsJson = document.getElementById('students-json');
    const studentsTableWrapper = document.getElementById('students-table-wrapper');
    const studentsTbody = document.getElementById('students-tbody');
    const studentsStatus = document.getElementById('students-status');

    // Elements - Rank
    const btnFetchRank = document.getElementById('btn-fetch-rank');
    const scoreInput = document.getElementById('score-input');
    const rankLoading = document.getElementById('rank-loading');
    const rankError = document.getElementById('rank-error');
    const rankResult = document.getElementById('rank-result');
    const rankJson = document.getElementById('rank-json');
    const resultCard = document.getElementById('result-card');
    const resultRank = document.getElementById('result-rank');
    const resultScore = document.getElementById('result-score');
    const resultMessage = document.getElementById('result-message');
    const toggleJson = document.getElementById('toggle-json');
    const rankStatus = document.getElementById('rank-status');

    // API Base URL
    const API_BASE = '/api';

    // Utility: Show/Hide elements
    function show(element) {
        element.classList.add('active');
    }
    function hide(element) {
        element.classList.remove('active');
    }
    function showError(element, message) {
        element.textContent = message;
        show(element);
    }
    function hideError(element) {
        hide(element);
        element.textContent = '';
    }

    // Utility: Set button loading state
    function setButtonLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.innerHTML = '<svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;"><circle cx="12" cy="12" r="10"/></svg> Đang tải...';
        } else {
            button.disabled = false;
        }
    }

    // Utility: Format JSON for display
    function formatJson(obj) {
        return JSON.stringify(obj, null, 2);
    }

    // ============ API: /api/students ============
    async function fetchStudents() {
        hideError(studentsError);
        hide(studentsData);
        hide(studentsTableWrapper);
        show(studentsLoading);
        setButtonLoading(btnFetchStudents, true);
        studentsStatus.textContent = '';

        try {
            const response = await fetch(`${API_BASE}/students`);
            const data = await response.json();

            hide(studentsLoading);

            if (!response.ok || data.ok !== 1) {
                throw new Error(data.msg || 'Lỗi không xác định');
            }

            // Success
            studentsStatus.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Thành công';
            studentsStatus.className = 'status-indicator success';

            // Display JSON
            studentsJson.textContent = formatJson(data);
            show(studentsData);

            // Display Table
            studentsTbody.innerHTML = '';
            data.students.forEach(student => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${student.id}</td>
                    <td>${escapeHtml(student.name)}</td>
                    <td>${escapeHtml(student.class)}</td>
                    <td>${student.score}</td>
                `;
                studentsTbody.appendChild(tr);
            });
            show(studentsTableWrapper);

        } catch (error) {
            hide(studentsLoading);
            showError(studentsError, `Lỗi: ${error.message}`);
            studentsStatus.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg> Thất bại';
            studentsStatus.className = 'status-indicator error';
        } finally {
            setButtonLoading(btnFetchStudents, false);
            btnFetchStudents.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 18a5 5 0 0 0-10 0M12 2v6"/></svg><span>Gọi API</span>';
        }
    }

    // ============ API: /api/rank ============
    async function fetchRank() {
        const scoreValue = scoreInput.value.trim();
        hideError(rankError);
        hide(rankResult);
        hide(rankJson);
        show(rankLoading);
        setButtonLoading(btnFetchRank, true);
        rankStatus.textContent = '';

        try {
            const response = await fetch(`${API_BASE}/rank?score=${encodeURIComponent(scoreValue)}`);
            const data = await response.json();

            hide(rankLoading);

            if (!response.ok || data.ok !== 1) {
                // Validation error from API
                throw new Error(data.msg || 'Lỗi không xác định');
            }

            // Success
            rankStatus.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Thành công';
            rankStatus.className = 'status-indicator success';

            // Update result card
            const rank = data.rank.toLowerCase().replace(' ', '-');
            resultCard.className = 'result-card ' + rank;
            resultRank.textContent = data.rank;
            resultScore.textContent = `Điểm: ${data.score}`;
            resultMessage.textContent = getRankMessage(data.rank, data.score);
            show(rankResult);

            // JSON
            rankJson.textContent = formatJson(data);
            if (toggleJson.checked) {
                show(rankJson);
            }

        } catch (error) {
            hide(rankLoading);
            showError(rankError, `Lỗi: ${error.message}`);
            rankStatus.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg> Thất bại';
            rankStatus.className = 'status-indicator error';
            scoreInput.classList.add('error-input');
        } finally {
            setButtonLoading(btnFetchRank, false);
            btnFetchRank.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg><span>Xếp loại</span>';
        }
    }

    function getRankMessage(rank, score) {
        switch (rank) {
            case 'Giỏi':
                return `Xuất sắc! Điểm ${score} đạt loại Giỏi.`;
            case 'Khá':
                return `Tốt! Điểm ${score} đạt loại Khá.`;
            case 'Trung bình':
                return `Đạt. Điểm ${score} đạt loại Trung bình.`;
            case 'Yếu':
                return `Cần cố gắng hơn. Điểm ${score} loại Yếu.`;
            default:
                return '';
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Event Listeners
    btnFetchStudents.addEventListener('click', fetchStudents);

    btnFetchRank.addEventListener('click', function() {
        scoreInput.classList.remove('error-input');
        fetchRank();
    });

    scoreInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            scoreInput.classList.remove('error-input');
            fetchRank();
        }
    });

    toggleJson.addEventListener('change', function() {
        if (this.checked) {
            show(rankJson);
        } else {
            hide(rankJson);
        }
    });

    // Auto-fetch students on load
    fetchStudents();

    console.log('Student API Demo initialized!');
});