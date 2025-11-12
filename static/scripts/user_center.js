document.addEventListener("DOMContentLoaded", () => {
  const saveBtn = document.getElementById("savePreferences");
  const themeSelect = document.getElementById("themeSelect");

  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      const selectedTheme = themeSelect.value;

      // Disable button while saving
      saveBtn.disabled = true;
      saveBtn.innerHTML = '<i class="bi bi-arrow-repeat spinner-border spinner-border-sm"></i> Saving...';

      try {
        const response = await fetch("/save_preferences", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ theme: selectedTheme }),
        });

        const result = await response.json();
        if (result.status === "success") {
          saveBtn.classList.remove("btn-danger");
          saveBtn.classList.add("btn-success");
          saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Saved!';

          // Update the theme immediately in the current page
          document.body.setAttribute('data-theme', selectedTheme);

          setTimeout(() => {
            saveBtn.innerHTML = '<i class="bi bi-save"></i> Save Changes';
            saveBtn.disabled = false;
          }, 2000);
        } else {
          throw new Error("Server error");
        }
      } catch (err) {
        console.error(err);
        saveBtn.classList.add("btn-danger");
        saveBtn.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Failed';
        setTimeout(() => {
          saveBtn.innerHTML = '<i class="bi bi-save"></i> Save Changes';
          saveBtn.disabled = false;
        }, 2500);
      }
    });
  }
});
