<template>
  <div class="kt-header__topbar-item kt-header__topbar-item--user">
    <!-- Logged -->
    <div class="kt-header__topbar-user" v-if="logged">
      <span class="kt-header__topbar-welcome kt-hidden-mobile">Hi,</span>
      <span class="kt-header__topbar-username kt-hidden-mobile"></span>
      <img class="kt-hidden" alt="Pic" src="/static/assets/media/users/300_25.jpg" />

      <div class="kt-notification__custom">
        <a
          href="custom_user_login-v2.html"
          target="_blank"
          class="btn btn-label-brand btn-sm btn-bold"
        >Logout</a>
      </div>
      <!--use below badge element instead the user avatar to display username's first letter(remove kt-hidden class to display it) -->
      <!-- <span
          class="kt-badge kt-badge--username kt-badge--unified-success kt-badge--lg kt-badge--rounded kt-badge--bold"
      >S</span>-->
    </div>

    <!-- Not Logged -->
    <div class="kt-header__topbar-user" v-if="!logged">
      <div class="kt-notification__custom">
        <a :href="link" class="btn btn-label-brand btn-sm btn-bold">Login</a>
      </div>
    </div>
  </div>

  <!--end: User Bar -->
</template>

<script>
export default {
  name: "UserLogin",
  data() {
    return {
      logged: false,
      link: "https://staging.zeroci.grid.tf/auth/login?provider=3bot",
      signedAttempt: this.$route.query.signedAttempt,
      name: null
    };
  },
  methods: {
    parseName() {
      let str = JSON.parse(this.signedAttempt);
      this.name = str.doubleName;
    }
  },
  computed: {
    formatName() {
      return this.name.replace(".3bot", "");
    }
  },
  created() {
    this.parseName();
  }
  //   this.$auth.handleAuthentication().then(data => {
  //     this.$router.push({ name: "Dashboard" });
  //   });
};
</script>
