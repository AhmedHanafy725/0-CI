<template>
  <div class="kt-header__topbar-wrapper" data-toggle="dropdown" data-offset="0px,0px">
    <div class="kt-header__topbar-user">
      <span class="kt-header__topbar-welcome kt-hidden-mobile">Hi,</span>
      <span class="kt-header__topbar-username kt-hidden-mobile">{{ formatUser }}</span>
      <img class="kt-hidden" alt="Pic" src="/static/assets/media/users/300_25.jpg" />

      <!--use below badge element instead the user avatar to display username's first letter(remove kt-hidden class to display it) -->
      <span
        class="kt-badge kt-badge--username kt-badge--unified-success kt-badge--lg kt-badge--rounded kt-badge--bold"
      >{{ userLogo }}</span>
    </div>
  </div>
</template>

<script>
import EventService from "../services/EventService";
export default {
  name: "LoginBtn",
  computed: {
    formatUser() {
      return this.$store.getters.formatUser;
    },
    userLogo() {
      return this.formatUser.charAt(0);
    }
  }
};
</script>
