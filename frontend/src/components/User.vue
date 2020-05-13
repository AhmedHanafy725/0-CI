<template>
  <div class="kt-header__topbar-item kt-header__topbar-item--user">
    <!-- Logged -->
    <Login-Btn v-if="$store.state.user !== null" />
    <User-Details v-if="$store.state.user !== null" />
    <!-- Not Logged -->
    <Logout-Btn v-if="$store.state.user == null" />
  </div>
</template>

<script>
import LoginBtn from "./LoginBtn";
import UserDetails from "./UserDetails";
import Logout from "./LogoutBtn";
export default {
  name: "User",
  components: {
    "Login-Btn": LoginBtn,
    "User-Details": UserDetails,
    "Logout-Btn": Logout
  }
};
</script>
