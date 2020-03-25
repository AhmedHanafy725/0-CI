<template>
  <li class="kt-menu__item" aria-haspopup="true">
    <router-link :to="'/projects/' + projectName" class="kt-menu__link">
      <span class="kt-menu__link-text">{{ project }}</span>
    </router-link>
  </li>
</template>
<script>
export default {
  name: "AsideProjects",
  props: ["project"],
  computed: {
    projectName() {
      return this.project.replace(' ', '%20')
    }
  }
};
</script>
