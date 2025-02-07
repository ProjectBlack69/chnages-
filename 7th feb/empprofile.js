document.addEventListener("DOMContentLoaded", function () {
  // Get CSRF token
  const csrftoken = document.querySelector("[name=csrf-token]").content;

  // Elements for modals and overlays
  const employeeOverlay = document.getElementById("employeeOverlay");
  const passwordOverlay = document.getElementById("passwordOverlay");
  const editModal = document.getElementById("employeeEditModal");
  const passwordModal = document.getElementById("passwordChangeModal");

  // Modal control for Employee Edit Modal
  function employeeOpenModal() {
    editModal.style.display = "block";
    employeeOverlay.style.display = "block";
  }

  //closes modal if clicked outside
  window.addEventListener("click", (event) => {
    if (event.target === employeeOverlay) {
      editModal.style.display = "none";
      employeeOverlay.style.display = "none";
    }
  });

  function employeeCloseModal() {
    editModal.style.display = "none";
    employeeOverlay.style.display = "none";
  }

  // Modal control for Password Change Modal
  function employeeOpenPasswordModal() {
    passwordModal.style.display = "block";
    passwordOverlay.style.display = "block";
  }

  //closes modal if clicked outside
  window.addEventListener("click", (event) => {
    if (event.target === passwordOverlay) {
      passwordModal.style.display = "none";
      passwordOverlay.style.display = "none";
    }
  });

  // Alert Box Modal
  let alertOverlay = document.querySelector(".modalBoxOverlay");
  let modalBox = document.querySelector(".modalBox");
  let alertTitle = document.getElementById("alertTitle");
  let alertMsg = document.getElementById("alertMsg");
  let alertClose = document.getElementById("modalOk");

  function showAlertModal(title, message) {
    alertOverlay.style.display = "block";
    modalBox.style.visibility = "visible";
    alertTitle.innerText = title;
    alertMsg.innerText = message;
  }

  function employeeClosePasswordModal() {
    passwordModal.style.display = "none";
    passwordOverlay.style.display = "none";
  }

  // Synchronize the modal fields with the profile
  const dobProfile = document.getElementById("employeeDob").innerText.trim();
  const dobEditField = document.getElementById("employeeEditDob");

  // Synchronize Date of Birth
  if (dobProfile && dobEditField) {
    const formattedDob = new Date(dobProfile).toISOString().split("T")[0]; // Format as YYYY-MM-DD
    dobEditField.value = formattedDob;
  }

  // Save Employee Details
  function employeeSaveChanges() {
    const dobEditField = document.getElementById("employeeEditDob");
    const dobProfile = document.getElementById("employeeDob").innerText.trim();

    // Only prepare data if there are changes
    const data = {
      full_name: document.getElementById("employeeEditName").value,
      employee_id: document.getElementById("employeeEditEmployeeId").value,
      job_title: document.getElementById("employeeEditJobTitle").value,
      department: document.getElementById("employeeEditDepartment").value,
      email: document.getElementById("employeeEditEmail").value,
      phone: document.getElementById("employeeEditPhone").value,
      skills: document.getElementById("employeeEditSkills").value,
      address: document.getElementById("employeeEditAddress").value,
      linkedin: document.getElementById("employeeEditLinkedin").value,
    };

    // Only add date_of_birth if it's not disabled and it's different from the profile value
    const dobValue = dobEditField.value;
    if (!dobEditField.disabled && dobValue && dobValue !== dobProfile) {
      data.date_of_birth = dobValue; // Add the DOB if it has been modified
    }

    fetch("/employee/update-details/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify(data),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showAlertModal("Successfull", "Details updated successfully!");
          alertTitle.style.color = "green";
          alertClose.style.backgroundColor = "green";
          alertClose.addEventListener("click", () => {
            location.reload(); // Reload the page to reflect updates
          });
        } else {
          showAlertModal(
            "Failed",
            "Failed to update details. Please try again."
          );
          alertTitle.style.color = "red";
          alertClose.style.backgroundColor = "red";
          alertClose.addEventListener("click", () => {
            location.reload(); // Reload the page to reflect updates
          });
        }
      })
      .catch((error) => console.error("Error:", error));
  }

  // Change Password
  function employeeChangePassword() {
    const data = {
      current_password: document.getElementById("currentPassword").value,
      new_password: document.getElementById("newPassword").value,
      confirm_password: document.getElementById("confirmNewPassword").value,
    };

    if (data.new_password !== data.confirm_password) {
      alert("New password and confirmation do not match!");
      return;
    }

    fetch("/employee/change-password/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify(data),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showAlertModal("Successfull", "Password changed successfully!");
          alertTitle.style.color = "green";
          alertClose.style.backgroundColor = "green";
          alertClose.addEventListener("click", () => {
            location.reload(); // Reload the page to reflect updates
          });
        } else {
          showAlertModal(
            "Failed",
            data.message || "Failed to change password. Please try again."
          );
          alertTitle.style.color = "red";
          alertClose.style.backgroundColor = "red";
          alertClose.addEventListener("click", () => {
            modalBox.style.visibility = "hidden";
            alertOverlay.style.display = "none";
          });
        }
      })
      .catch((error) => console.error("Error:", error));
  }


  // Attach event listeners
  document
    .querySelector(".employee-edit-btn")
    .addEventListener("click", employeeOpenModal);
  document
    .querySelector("#employeeEditModal .cancel-btn")
    .addEventListener("click", employeeCloseModal);
  document
    .querySelector(".employee-password-btn")
    .addEventListener("click", employeeOpenPasswordModal);
  document
    .querySelector("#passwordChangeModal .cancel-btn")
    .addEventListener("click", employeeClosePasswordModal);
  document
    .querySelector("#employeeEditModal .save-btn")
    .addEventListener("click", employeeSaveChanges);
  document
    .querySelector("#passwordChangeModal .save-btn")
    .addEventListener("click", employeeChangePassword);
  document
    .querySelector("#employeeProfileImage")
    .addEventListener("click", employeeChangeProfilePicture);
});

// Function to get CSRF token from cookies
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          // Check if this cookie is the CSRF token
          if (cookie.startsWith(name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}

function triggerEmployeeFileInput() {
  document.getElementById('employeeProfilePictureInput').click();
}

function handleEmployeeFileChange(event) {
  const file = event.target.files[0];
  if (file) {
      const formData = new FormData();
      formData.append('profile_picture', file);

      fetch('/employee/update-profile-picture/', {
          method: 'POST',
          body: formData,
          headers: {
              'X-CSRFToken': getCookie('csrftoken'), 
              'X-Requested-With': 'XMLHttpRequest'
          }
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              document.getElementById('employeeProfileImage').src = data.url;
          }
          alert(data.success ? 'Profile updated successfully' : data.error);
      })
      .catch(error => {
          console.error('Error:', error);
          alert('An error occurred. Please try again.');
      });
  }
}
