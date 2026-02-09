/**
 * filter.js - Task filtering logic
 * Xử lý lọc công việc theo các tiêu chí khác nhau
 */

let selectedMonthFilter = null; // Store selected month for filtering

/**
 * Get today's date at midnight
 */
function getToday() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today;
}

/**
 * Get start of current week (Sunday at midnight)
 */
function getStartOfWeek() {
  const today = new Date();
  const day = today.getDay();
  const diff = today.getDate() - day;
  const start = new Date(today.setDate(diff));
  start.setHours(0, 0, 0, 0);
  return start;
}

/**
 * Get start of current month (1st at midnight)
 */
function getStartOfMonth() {
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth(), 1);
  start.setHours(0, 0, 0, 0);
  return start;
}

/**
 * Filter todos by type: 'all', 'today', 'week', 'month', 'done', 'pending'
 */
function filterTodos(filterType) {
  const rows = document.querySelectorAll('.todo-row');
  const today = getToday();
  const weekStart = getStartOfWeek();
  const monthStart = getStartOfMonth();
  
  // Calculate week end (7 days after start)
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekEnd.getDate() + 7);
  
  // Calculate month end
  const monthEnd = new Date(monthStart);
  monthEnd.setMonth(monthEnd.getMonth() + 1);

  rows.forEach(row => {
    const isDone = row.getAttribute('data-is-done') === 'true';
    const dueDateStr = row.getAttribute('data-due-date');
    const dueDate = dueDateStr ? new Date(dueDateStr) : null;

    let show = false;

    switch(filterType) {
      case 'all':
        show = true;
        break;
      case 'today':
        show = dueDate && dueDate >= today && dueDate < new Date(today.getTime() + 24*60*60*1000);
        break;
      case 'week':
        show = dueDate && dueDate >= weekStart && dueDate < weekEnd;
        break;
      case 'month':
        show = dueDate && dueDate >= monthStart && dueDate < monthEnd;
        break;
      case 'done':
        show = isDone;
        break;
      case 'pending':
        show = !isDone;
        break;
    }

    // If a specific month filter is selected, apply it
    if (selectedMonthFilter && show) {
      show = dueDateStr && dueDateStr.startsWith(selectedMonthFilter);
    }

    row.style.display = show ? '' : 'none';
  });
}

/**
 * Initialize tab click handlers for filtering
 */
function initFilterTabHandlers() {
  document.querySelectorAll('#todoTabs button').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const tabId = btn.id.replace('-tab', '');
      filterTodos(tabId);
    });
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initFilterTabHandlers);
} else {
  initFilterTabHandlers();
}
