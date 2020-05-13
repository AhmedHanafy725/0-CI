<template>
  <div class="kt-header__topbar-user">
    <div class="kt-notification__custom">
      <a :href="link" class="btn btn-label-brand btn-sm btn-bold">Login</a>
    </div>
  </div>
</template>

<script>
export default {
  name: "LogoutBtn",
  data() {
    return {
      link: "/auth/login?provider=3bot"
    };
  }
};
</script>
