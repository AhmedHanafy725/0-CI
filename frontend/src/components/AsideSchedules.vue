<template>
  <li class="kt-menu__item" aria-haspopup="true">
    <router-link :to="'/schedules/' + schedule" class="kt-menu__link">
      <span class="kt-menu__link-text">{{ schedule }}</span>
    </router-link>
  </li>
</template>

<script>
export default {
  name: "AsideSchedules",
  props: ["schedule"]
};
</script>
