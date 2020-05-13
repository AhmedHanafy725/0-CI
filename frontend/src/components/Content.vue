<template>
  <div class="kt-content kt-grid__item kt-grid__item--fluid" id="kt_content">
    <router-view />
  </div>
</template>

<script>
export default {
  name: "Content"
};
</script>

<style scoped>
.kt-content {
  background-color: #eeeef4;
  min-height: 80vh;
}
</style>
