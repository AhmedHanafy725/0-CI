<template>
  <li class="kt-menu__item" aria-haspopup="true">
    <router-link :to="'/schedules/' + scheduleName" class="kt-menu__link">
      <span class="kt-menu__link-text">{{ schedule }}</span>
    </router-link>
  </li>
</template>
<script>
export default {
  name: "AsideSchedules",
  props: ["schedule"],
  computed: {
    scheduleName() {
      return this.schedule.replace(" ", "%20");
    }
  }
};
</script>
