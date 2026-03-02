/**
 * calendar.js - Main calendar display and navigation
 * Xử lý hiển thị lịch, điều hướng tháng/năm
 */

let calendarYear = new Date().getFullYear();
let calendarMonth = new Date().getMonth();

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
  const adjustedStartDay = (startDay + 6) % 7; // chuyển sang tuần bắt đầu từ Thứ 2
  const daysInMonth = new Date(year, month+1, 0).getDate();
  const today = new Date();

  const monthNames = ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
                      'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'];

  const header = document.createElement('div');
  header.className = 'mb-3 text-center fw-bold';
  header.innerHTML = `<h6>${monthNames[month]} ${year}</h6>`;
  cal.appendChild(header);

  const daysHeader = document.createElement('div');
  daysHeader.className = 'calendar-weekday-row';
  const dayNames = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'];
  dayNames.forEach(day => {
    const d = document.createElement('div');
    d.className = 'calendar-weekday text-center';
    d.innerText = day;
    daysHeader.appendChild(d);
  });
  cal.appendChild(daysHeader);

  const grid = document.createElement('div');
  grid.className = 'calendar-grid';

  // Empty slots before month starts
  for (let i = 0; i < adjustedStartDay; i++) {
    const placeholder = document.createElement('div');
    placeholder.className = 'calendar-day-card calendar-day-placeholder';
    placeholder.setAttribute('aria-hidden', 'true');
    grid.appendChild(placeholder);
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const cell = document.createElement('div');
    cell.className = 'calendar-day-card';
    cell.tabIndex = 0;

    const dateStr = `${year}-${(month+1).toString().padStart(2,'0')}-${d.toString().padStart(2,'0')}`;
    const isToday = today.getFullYear() === year && today.getMonth() === month && today.getDate() === d;

    const headerRow = document.createElement('div');
    headerRow.className = 'calendar-day-header';

    const dayNumber = document.createElement('div');
    dayNumber.className = 'calendar-day-number';
    dayNumber.innerText = d.toString();
    headerRow.appendChild(dayNumber);

    cell.appendChild(headerRow);

    if (isToday) {
      cell.classList.add('calendar-day-current');
      const todayChip = document.createElement('span');
      todayChip.className = 'calendar-day-chip';
      todayChip.innerText = 'Hôm nay';
      cell.appendChild(todayChip);
    }

    const items = todos.filter(t => t.due_date && t.due_date.startsWith(dateStr));
    if (items.length) {
      cell.classList.add('calendar-day-has-tasks');
    }

    const body = document.createElement('div');
    body.className = 'calendar-day-body';

    const count = document.createElement('div');
    count.className = 'calendar-day-count';
    count.innerText = items.length ? items.length.toString() : '0';
    if (items.length) {
      count.classList.add('calendar-day-count-active');
    }
    body.appendChild(count);

    cell.appendChild(body);

    const targetUrl = `/dashboard/day/${dateStr}`;
    cell.dataset.href = targetUrl;

    const stretchedLink = document.createElement('a');
    stretchedLink.href = targetUrl;
    stretchedLink.className = 'stretched-link';
    stretchedLink.setAttribute('aria-label', `Mở công việc ngày ${d}`);
    stretchedLink.tabIndex = -1;
    cell.appendChild(stretchedLink);

    cell.addEventListener('click', () => {
      window.location.href = targetUrl;
    });

    cell.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        window.location.href = targetUrl;
      }
    });

    grid.appendChild(cell);
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

window.addEventListener('todos:changed', () => {
  renderCalendar(calendarYear, calendarMonth);
  updateMonthYearDisplay();
});
