<template>
  <div class="kt-header__topbar-item kt-header__topbar-item--user">
    <!-- Logged -->
    <Login-btn v-if="$store.state.user !== null" />
    <!-- Not Logged -->
    <Logout-btn v-if="$store.state.user == null" />
  </div>

  <!--end: User Bar -->
</template>

<script>
import LoginBtn from "./LoginBtn";
import LogoutBtn from "./LogoutBtn";
export default {
  name: "UserLogin",
  components: {
    "Login-btn": LoginBtn,
    "Logout-btn": LogoutBtn
  }
};
</script>
