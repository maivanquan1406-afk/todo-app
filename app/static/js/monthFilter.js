/**
 * monthFilter.js - Month/year filter for task list
 * Cho phép lọc công việc theo tháng cụ thể
 */

/**
 * Initialize month selector handlers
 */
function initMonthFilter() {
  // Month selector change handler
  const monthYearSelelector = document.getElementById('monthYearSelector');
  if (monthYearSelelector) {
    monthYearSelelector.addEventListener('change', function() {
      const monthYearValue = this.value; // format: YYYY-MM
      if (monthYearValue) {
        selectedMonthFilter = monthYearValue;
        // Get current active tab and apply filter
        const activeTab = document.querySelector('.nav-link.active');
        if (activeTab) {
          const tabId = activeTab.id.replace('-tab', '');
          filterTodos(tabId);
        }
      }
    });
  }

  // Clear month filter button
  const clearMonthFilterBtn = document.getElementById('clearMonthFilterBtn');
  if (clearMonthFilterBtn) {
    clearMonthFilterBtn.addEventListener('click', function() {
      document.getElementById('monthYearSelector').value = '';
      selectedMonthFilter = null;
      // Reapply current filter
      const activeTab = document.querySelector('.nav-link.active');
      if (activeTab) {
        const tabId = activeTab.id.replace('-tab', '');
        filterTodos(tabId);
      }
    });
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMonthFilter);
} else {
  initMonthFilter();
}
