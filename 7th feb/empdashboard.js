document.addEventListener('DOMContentLoaded', function () {
    const shiftTimeElement = document.getElementById('shift-progress');
    const progressBar = document.getElementById('shift-progress');
    const countdownTimer = document.getElementById('countdown-timer');
    const status = document.getElementById('status');

    if (shiftTimeElement && progressBar && countdownTimer) {
        const startTimeStr = shiftTimeElement.getAttribute("data-start-time");
        const endTimeStr = shiftTimeElement.getAttribute("data-end-time");
        const virtualTimeStr = shiftTimeElement.getAttribute("data-virtual-time");

        const startTime = new Date(startTimeStr);
        const endTime = new Date(endTimeStr);
        let virtualTime = new Date(virtualTimeStr);

        console.log("Start Time:", startTime);
        console.log("End Time:", endTime);
        console.log("Virtual Time:", virtualTime);

        if (isNaN(startTime) || isNaN(endTime) || isNaN(virtualTime)) {
            countdownTimer.textContent = "Invalid Shift Time";
            progressBar.style.width = "0%";
            return;
        }

        function updateProgressAndCountdown() {
            // Simulate the passage of virtual time by incrementing every second
            virtualTime = new Date(virtualTime.getTime() + 1000); // Add 1 second to virtual time

            const now = virtualTime;  // Use virtual time instead of real time

            if (now >= endTime) {
                status.textcontent = "Completed";
                progressBar.style.width = "100%";
                countdownTimer.textContent = "Shift Completed";
                return;
            }

            if (now < startTime) {
                progressBar.style.width = "0%";
                countdownTimer.textContent = "Shift Not Started";
                return;
            }

            const totalShiftTime = endTime - startTime;
            const elapsedTime = now - startTime;
            const progress = Math.min((elapsedTime / totalShiftTime) * 100, 100);
            progressBar.style.width = `${progress}%`;

            const timeDiff = endTime - now;
            const hours = Math.floor(timeDiff / (1000 * 60 * 60));
            const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);

            countdownTimer.textContent = `${hours}h ${minutes}m ${seconds}s`;
        }

        setInterval(updateProgressAndCountdown, 1000); // Update every second
        updateProgressAndCountdown(); // Initial call to set values
    }
});



function toggleNotificationDropdown() {
    const dropdown = document.getElementById("notificationDropdown");
    dropdown.classList.toggle("show"); // Toggle the dropdown visibility
}

function markNotificationsRead() {
    fetch('/employee/mark-all-notifications-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update unread count badge
            const badge = document.querySelector('.notification-badge');
            if (badge) {
                badge.textContent = 0;
                badge.style.display = 'none'; // Hide the badge if unread count is zero
            }

            // Update dropdown content
            const dropdownContent = document.getElementById('notificationDropdown');
            if (data.unread_count === 0) {
                dropdownContent.innerHTML = `
                    <p>No new notifications.</p>
                    <div class="actions">
                        <a href="/employee/notifications/" class="view-all">View All</a>
                    </div>
                `;
            }
        } else {
            console.error('Error:', data.message);
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
}

// Close the dropdown when clicking outside
window.onclick = function (event) {
    const dropdown = document.getElementById("notificationDropdown");
    const notificationButton = document.querySelector('.dropbtn');
    if (!event.target.matches('.dropbtn') && !event.target.closest('.notification-dropdown')) {
        dropdown.classList.remove('show');
    }
};

document.addEventListener('DOMContentLoaded', function () {
    // Get references to the form elements and the button
    const shiftDateInput = document.getElementById('shift-date');
    const swapReasonTextarea = document.getElementById('swap-reason');
    const submitButton = document.getElementById('submit-btn');

    // Function to validate the form and enable/disable the submit button
    function validateForm() {
        // Check if both fields are filled out (shift date and swap reason)
        if (shiftDateInput.value.trim() !== '' && swapReasonTextarea.value.trim() !== '') {
            submitButton.disabled = false;  // Enable the button
        } else {
            submitButton.disabled = true;   // Disable the button
        }
    }

    // Add event listeners to monitor changes in the form fields
    shiftDateInput.addEventListener('input', validateForm);
    swapReasonTextarea.addEventListener('input', validateForm);
});
const body = document.querySelector("body"),
      sidebar = body.querySelector("nav");
      sidebarToggle = body.querySelector(".sidebar-toggle");

let getStatus = localStorage.getItem("status");
if(getStatus && getStatus ==="close"){
    sidebar.classList.toggle("close");
}

sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("close");
    if(sidebar.classList.contains("close")){
        localStorage.setItem("status", "close");
    }else{
        localStorage.setItem("status", "open");
    }
})

