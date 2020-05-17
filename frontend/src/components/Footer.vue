<template>
  <div class="kt-footer kt-grid__item kt-grid kt-grid--desktop kt-grid--ver-desktop">
    <div class="kt-footer__copyright">
      2020&nbsp;&copy;&nbsp;
      <a href="#" class="kt-link">ThreeFold</a>
    </div>
    <div class="kt-footer__menu">
      <a href="#" class="kt-footer__menu-link kt-link">About</a>
      <a href="#" class="kt-footer__menu-link kt-link">Team</a>
      <a href="#" class="kt-footer__menu-link kt-link">Contact</a>
    </div>
  </div>
</template>

<script>
export default {
  name: "Footer"
};
</script>

<style scoped>
.kt-footer {
  position: fixed;
  bottom: 0;
  left: 255px;
  right: 0;
  z-index: 90;
}
</style>
