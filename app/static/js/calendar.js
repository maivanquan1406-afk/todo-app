/**
 * calendar.js - Main calendar display and navigation
 * Xử lý hiển thị lịch, điều hướng tháng/năm
 */

let calendarYear = new Date().getFullYear();
let calendarMonth = new Date().getMonth();
let selectedCalendarDate = null;

/**
 * Update month/year display text
 */
function updateMonthYearDisplay() {
  const today = new Date();
  const isCurrentMonth = calendarYear === today.getFullYear() && calendarMonth === today.getMonth();
  
  if (isCurrentMonth) {
    document.getElementById('monthYearDisplay').innerText = 'Tháng này';
  } else {
    const monthNames = ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
                        'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'];
    document.getElementById('monthYearDisplay').innerText = `${monthNames[calendarMonth]} ${calendarYear}`;
  }
}

/**
 * Render calendar with task counts
 */
function renderCalendar(year, month) {
  const cal = document.getElementById('calendar');
  cal.innerHTML = '';
  const first = new Date(year, month, 1);
  const startDay = first.getDay();
  const daysInMonth = new Date(year, month+1, 0).getDate();

  const monthNames = ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
                      'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'];

  const header = document.createElement('div');
  header.className = 'mb-3 text-center fw-bold';
  header.innerHTML = `<h6>${monthNames[month]} ${year}</h6>`;
  cal.appendChild(header);

  const daysHeader = document.createElement('div');
  daysHeader.className = 'd-grid mb-2';
  daysHeader.style.gridTemplateColumns = 'repeat(7, 1fr)';
  const dayNames = ['CN', 'Th 2', 'Th 3', 'Th 4', 'Th 5', 'Th 6', 'Th 7'];
  dayNames.forEach(day => {
    const d = document.createElement('div');
    d.className = 'text-center text-muted fw-bold small';
    d.innerText = day;
    daysHeader.appendChild(d);
  });
  cal.appendChild(daysHeader);

  const grid = document.createElement('div');
  grid.className = 'd-grid';
  grid.style.gridTemplateColumns = 'repeat(7, 1fr)';
  grid.style.gap = '6px';

  // Empty slots before month starts
  for (let i = 0; i < startDay; i++) {
    const e = document.createElement('div');
    grid.appendChild(e);
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const cell = document.createElement('div');
    cell.className = 'calendar-day p-2 border rounded text-center';
    cell.style.minHeight = '80px';
    cell.style.cursor = 'pointer';
    cell.style.transition = 'all 0.3s ease';

    const dateStr = `${year}-${(month+1).toString().padStart(2,'0')}-${d.toString().padStart(2,'0')}`;
    const dayTitle = document.createElement('div');
    dayTitle.className = 'fw-bold mb-2';
    dayTitle.innerText = d;
    cell.appendChild(dayTitle);

    const items = todos.filter(t => t.due_date && t.due_date.startsWith(dateStr));
    if (items.length) {
      const badge = document.createElement('span');
      badge.className = 'badge bg-primary';
      badge.innerText = items.length + ' công việc';
      cell.appendChild(badge);
      cell.style.backgroundColor = '#e7f3ff';
    }

    cell.addEventListener('mouseover', () => {
      cell.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
      cell.style.borderColor = '#0d6efd';
    });

    cell.addEventListener('mouseout', () => {
      cell.style.boxShadow = 'none';
      cell.style.borderColor = '';
    });

    cell.addEventListener('click', () => {
      // Store the selected date
      selectedCalendarDate = dateStr;
      
      // Clear all active states
      document.querySelectorAll('.calendar-day').forEach(c => {
        c.style.backgroundColor = '';
        c.style.borderColor = '';
        c.style.borderWidth = '';
      });
      
      // Highlight selected cell
      cell.style.backgroundColor = '#0d6efd';
      cell.style.color = 'white';
      cell.style.borderColor = '#0d6efd';
      cell.style.borderWidth = '2px';
      
      // Filter todos for this date
      const rows = document.querySelectorAll('.todo-row');
      let hasItems = false;
      rows.forEach(row => {
        const dueDateStr = row.getAttribute('data-due-date');
        if (dueDateStr && dueDateStr.startsWith(dateStr)) {
          row.style.display = '';
          hasItems = true;
        } else {
          row.style.display = 'none';
        }
      });
      
      // Scroll to task list
      const taskCard = document.querySelector('.card-header.bg-success');
      if (taskCard) {
        taskCard.scrollIntoView({behavior:'smooth', block:'start'});
      }
    });

    grid.appendChild(cell);
    
    // Highlight if this is the selected date
    if (selectedCalendarDate && dateStr === selectedCalendarDate) {
      cell.style.backgroundColor = '#0d6efd';
      cell.style.color = 'white';
      cell.style.borderColor = '#0d6efd';
      cell.style.borderWidth = '2px';
    }
  }

  cal.appendChild(grid);
}

/**
 * Initialize calendar and month selector
 */
function initCalendar() {
  const today = new Date();
  renderCalendar(today.getFullYear(), today.getMonth());
  updateMonthYearDisplay();

  // Previous month button
  document.getElementById('prevMonth').addEventListener('click', () => {
    calendarMonth--;
    if (calendarMonth < 0) {
      calendarMonth = 11;
      calendarYear--;
    }
    renderCalendar(calendarYear, calendarMonth);
    updateMonthYearDisplay();
  });

  // Next month button
  document.getElementById('nextMonth').addEventListener('click', () => {
    calendarMonth++;
    if (calendarMonth > 11) {
      calendarMonth = 0;
      calendarYear++;
    }
    renderCalendar(calendarYear, calendarMonth);
    updateMonthYearDisplay();
  });

  // Month/Year selector modal
  const monthSelector = document.getElementById('monthSelector');
  const yearInput = document.getElementById('yearInput');
  const currentMonthBtn = document.getElementById('currentMonth');

  currentMonthBtn.addEventListener('click', () => {
    yearInput.value = calendarYear;
    document.querySelectorAll('.month-btn').forEach(btn => {
      const month = parseInt(btn.getAttribute('data-month'));
      if (month === calendarMonth) {
        btn.classList.remove('btn-outline-primary');
        btn.classList.add('btn-primary');
      } else {
        btn.classList.add('btn-outline-primary');
        btn.classList.remove('btn-primary');
      }
    });
    monthSelector.style.display = monthSelector.style.display === 'none' ? 'block' : 'none';
  });

  document.getElementById('cancelSelector').addEventListener('click', () => {
    monthSelector.style.display = 'none';
  });

  document.getElementById('yearMinus').addEventListener('click', () => {
    yearInput.value = Math.max(2000, parseInt(yearInput.value) - 1);
  });

  document.getElementById('yearPlus').addEventListener('click', () => {
    yearInput.value = Math.min(2100, parseInt(yearInput.value) + 1);
  });

  document.querySelectorAll('.month-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.month-btn').forEach(b => {
        b.classList.add('btn-outline-primary');
        b.classList.remove('btn-primary');
      });
      btn.classList.remove('btn-outline-primary');
      btn.classList.add('btn-primary');
    });
  });

  document.getElementById('applySelector').addEventListener('click', () => {
    const selectedMonth = document.querySelector('.month-btn.btn-primary');
    if (selectedMonth) {
      calendarYear = parseInt(yearInput.value);
      calendarMonth = parseInt(selectedMonth.getAttribute('data-month'));
      renderCalendar(calendarYear, calendarMonth);
      updateMonthYearDisplay();
      monthSelector.style.display = 'none';
    }
  });

  // Close selector when clicking outside
  document.addEventListener('click', (e) => {
    if (!monthSelector.contains(e.target) && !currentMonthBtn.contains(e.target)) {
      monthSelector.style.display = 'none';
    }
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initCalendar);
} else {
  initCalendar();
}
