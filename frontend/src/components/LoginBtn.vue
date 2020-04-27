<template>
  <div class="kt-header__topbar-user">
    <span class="kt-header__topbar-welcome kt-hidden-mobile">Hi,</span>
    <span class="kt-header__topbar-username kt-hidden-mobile">{{ formatUser }}</span>
    <img class="kt-hidden" alt="Pic" src="/static/media/users/300_25.jpg" />

    <div class="kt-notification__custom">
      <a @click="logout()" target="_blank" class="btn btn-label-brand btn-sm btn-bold">Logout</a>
    </div>
    <!--use below badge element instead the user avatar to display username's first letter(remove kt-hidden class to display it) -->
    <!-- <span
          class="kt-badge kt-badge--username kt-badge--unified-success kt-badge--lg kt-badge--rounded kt-badge--bold"
    >S</span>-->
  </div>
</template>

<script>
import EventService from "../services/EventService";
export default {
  name: "LoginBtn",
  methods: {
    logout() {
      this.$store.commit("SET_USER", null);
      this.$store.commit("SET_EMAIL", null);
      this.$store.commit("SET_PERMISSION", null);
      if (window.localStorage) {
        window.localStorage.setItem("user", null);
        window.localStorage.setItem("email", null);
        window.localStorage.setItem("permission", null);
      }
      EventService.logout();
    }
  },
  computed: {
    formatUser() {
      return this.$store.getters.formatUser;
    }
  }
};
</script>
