<template>
  <!-- begin:: Page -->
  <div class="kt-grid kt-grid--ver kt-grid--root">
    <div class="kt-grid__item kt-grid__item--fluid kt-grid kt-error-v1">
      <div class="kt-error-v1__container">
        <h1 class="kt-error-v1__number">{{ error_no }}</h1>
        <p class="kt-error-v1__desc">{{ error_desc }}</p>
      </div>
    </div>
  </div>

  <!-- end:: Page -->
</template>
<script>
export default {
  name: "Error",
  data() {
    return {
      error_no: "Oops...",
      error_desc: "Looks like something went wrong."
    };
  }
};
</script>
