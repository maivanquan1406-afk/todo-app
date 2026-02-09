/**
 * datepicker.js - Custom date/time picker modal
 * Xử lý chọn ngày và giờ cho công việc
 */

let pickerYear = new Date().getFullYear();
let pickerMonth = new Date().getMonth();
let selectedDay = null;

const dateTimePicker = document.getElementById('dateTimePicker');
const dueDateDisplay = document.getElementById('due_date_display');
const dueDateHidden = document.getElementById('due_date');

/**
 * Render calendar grid in date picker
 */
function renderPickerCalendar() {
  const cal = document.getElementById('pickerCalendarGrid');
  cal.innerHTML = '';
  const first = new Date(pickerYear, pickerMonth, 1);
  const startDay = first.getDay();
  const daysInMonth = new Date(pickerYear, pickerMonth + 1, 0).getDate();

  const monthNames = ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
                      'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'];

  // Month/Year display
  document.getElementById('pickerMonthYear').innerText = `${monthNames[pickerMonth]} ${pickerYear}`;

  // Days header
  const daysHeader = document.createElement('div');
  daysHeader.className = 'd-grid mb-2';
  daysHeader.style.gridTemplateColumns = 'repeat(7, 1fr)';
  daysHeader.style.gap = '4px';
  const dayNames = ['CN', 'Th 2', 'Th 3', 'Th 4', 'Th 5', 'Th 6', 'Th 7'];
  dayNames.forEach(day => {
    const d = document.createElement('div');
    d.className = 'text-center text-muted fw-bold small';
    d.innerText = day;
    daysHeader.appendChild(d);
  });
  cal.appendChild(daysHeader);

  // Days grid
  const grid = document.createElement('div');
  grid.className = 'd-grid';
  grid.style.gridTemplateColumns = 'repeat(7, 1fr)';
  grid.style.gap = '4px';

  // Empty slots for days before month starts
  for (let i = 0; i < startDay; i++) {
    const e = document.createElement('div');
    grid.appendChild(e);
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const cell = document.createElement('div');
    cell.className = 'text-center p-2 border rounded cursor-pointer picker-day';
    cell.style.cursor = 'pointer';
    cell.style.transition = 'all 0.2s ease';
    cell.style.fontWeight = '500';
    cell.innerText = d;
    cell.setAttribute('data-day', d);

    cell.addEventListener('mouseover', () => {
      cell.style.backgroundColor = '#e7f3ff';
      cell.style.borderColor = '#0d6efd';
    });

    cell.addEventListener('mouseout', () => {
      if (selectedDay !== d || pickerYear !== new Date().getFullYear() || pickerMonth !== new Date().getMonth()) {
        cell.style.backgroundColor = '';
        cell.style.borderColor = '';
      }
    });

    cell.addEventListener('click', () => {
      // Unselect previous day
      document.querySelectorAll('.picker-day').forEach(c => {
        c.style.backgroundColor = '';
        c.style.borderColor = '';
      });

      // Select new day
      selectedDay = d;
      cell.style.backgroundColor = '#0d6efd';
      cell.style.color = 'white';
      cell.style.borderColor = '#0d6efd';

      // Update display
      const dateStr = `${d}/${pickerMonth + 1}/${pickerYear}`;
      const hour = document.getElementById('pickerHour').value.padStart(2, '0');
      const minute = document.getElementById('pickerMinute').value.padStart(2, '0');
      document.getElementById('pickerSelectedDate').innerText = `${dateStr} ${hour}:${minute}`;
    });

    grid.appendChild(cell);
  }

  cal.appendChild(grid);
}

/**
 * Initialize date/time picker
 */
function initDatePicker() {
  // Open picker when clicking on due_date_display
  dueDateDisplay.addEventListener('click', () => {
    const backdrop = document.getElementById('pickerBackdrop');
    backdrop.classList.add('show');
    dateTimePicker.classList.add('show');
    
    renderPickerCalendar();
  });

  // Picker month navigation
  document.getElementById('pickerPrevMonth').addEventListener('click', () => {
    pickerMonth--;
    if (pickerMonth < 0) {
      pickerMonth = 11;
      pickerYear--;
    }
    selectedDay = null;
    renderPickerCalendar();
  });

  document.getElementById('pickerNextMonth').addEventListener('click', () => {
    pickerMonth++;
    if (pickerMonth > 11) {
      pickerMonth = 0;
      pickerYear++;
    }
    selectedDay = null;
    renderPickerCalendar();
  });

  // Update time display when time inputs change
  document.getElementById('pickerHour').addEventListener('change', () => {
    if (selectedDay) {
      const dateStr = `${selectedDay}/${pickerMonth + 1}/${pickerYear}`;
      const hour = document.getElementById('pickerHour').value.padStart(2, '0');
      const minute = document.getElementById('pickerMinute').value.padStart(2, '0');
      document.getElementById('pickerSelectedDate').innerText = `${dateStr} ${hour}:${minute}`;
    }
  });

  document.getElementById('pickerMinute').addEventListener('change', () => {
    if (selectedDay) {
      const dateStr = `${selectedDay}/${pickerMonth + 1}/${pickerYear}`;
      const hour = document.getElementById('pickerHour').value.padStart(2, '0');
      const minute = document.getElementById('pickerMinute').value.padStart(2, '0');
      document.getElementById('pickerSelectedDate').innerText = `${dateStr} ${hour}:${minute}`;
    }
  });

  // Apply selection
  document.getElementById('applyPickerBtn').addEventListener('click', () => {
    if (selectedDay) {
      const day = selectedDay.toString().padStart(2, '0');
      const month = (pickerMonth + 1).toString().padStart(2, '0');
      const year = pickerYear;
      const hour = document.getElementById('pickerHour').value.padStart(2, '0');
      const minute = document.getElementById('pickerMinute').value.padStart(2, '0');

      const dateStr = `${day}/${month}/${year}`;
      const timeStr = `${hour}:${minute}`;
      dueDateDisplay.value = `${dateStr} ${timeStr}`;

      // Set the hidden input for form submission (ISO format)
      const isoDate = `${year}-${month}-${day}T${hour}:${minute}`;
      dueDateHidden.value = isoDate;

      const backdrop = document.getElementById('pickerBackdrop');
      dateTimePicker.classList.remove('show');
      backdrop.classList.remove('show');
      selectedDay = null;
    }
  });

  // Cancel picker
  document.getElementById('cancelPickerBtn').addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const backdrop = document.getElementById('pickerBackdrop');
    dateTimePicker.classList.remove('show');
    backdrop.classList.remove('show');
    selectedDay = null;
  });

  document.getElementById('closePickerBtn').addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const backdrop = document.getElementById('pickerBackdrop');
    dateTimePicker.classList.remove('show');
    backdrop.classList.remove('show');
    selectedDay = null;
  });

  // Close picker when clicking on backdrop only
  document.getElementById('pickerBackdrop').addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const backdrop = document.getElementById('pickerBackdrop');
    dateTimePicker.classList.remove('show');
    backdrop.classList.remove('show');
  });

  // Prevent clicks inside picker from closing it
  document.getElementById('dateTimePicker').addEventListener('click', (e) => {
    e.stopPropagation();
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDatePicker);
} else {
  initDatePicker();
}
