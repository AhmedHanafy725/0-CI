<template>
  <div
    class="dropdown-menu dropdown-menu-fit dropdown-menu-right dropdown-menu-anim dropdown-menu-top-unround dropdown-menu-xl"
  >
    <!--begin: Head -->
    <div
      class="kt-user-card kt-user-card--skin-dark kt-notification-item-padding-x"
      style="background-image: url(/static/assets/media/misc/bg-1.jpg)"
    >
      <div class="kt-user-card__avatar">
        <img class="kt-hidden" alt="Pic" src="/static/assets/media/users/300_25.jpg" />

        <!--use below badge element instead the user avatar to display username's first letter(remove kt-hidden class to display it) -->
        <span class="kt-badge kt-badge--lg kt-badge--rounded kt-badge--bold kt-font-success">{{ userLogo }}</span>
      </div>
      <div class="kt-user-card__name">{{ formatUser }}</div>
    </div>

    <!--end: Head -->

    <!--begin: Navigation -->
    <div class="kt-notification">
      <a href="#" class="kt-notification__item">
        <div class="kt-notification__item-icon">
          <i class="flaticon2-calendar-3 kt-font-success"></i>
        </div>
        <div class="kt-notification__item-details">
          <div class="kt-notification__item-title kt-font-bold">Configuration</div>
          <!-- <div class="kt-notification__item-time">Account settings and more</div> -->
        </div>
      </a>

      <div class="kt-notification__custom">
        <a @click="logout()" class="btn btn-label-brand btn-sm btn-bold">LogOut</a>
      </div>
    </div>

    <!--end: Navigation -->
  </div>
</template>

<script>
import EventService from "../services/EventService";
export default {
  name: "UserDetails",
  methods: {
    logout() {
      this.$store.commit("SET_USER", null);
      this.$store.commit("SET_EMAIL", null);
      this.$store.commit("SET_PERMISSION", null);
      EventService.logout().then(response => {
        this.$router.push("/");
      });
    }
  },
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

<style scoped>
.kt-notification .kt-notification__item:after {
  display: none;
}
</style>
