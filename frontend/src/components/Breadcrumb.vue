<template>
  <!-- begin:: Content Head -->
  <div class="kt-subheader kt-grid__item" id="kt_subheader">
    <div class="kt-subheader__main">
      <h3 class="kt-subheader__title">Dashboard</h3>
      <span class="kt-subheader__separator kt-hidden"></span>
      <div class="kt-subheader__breadcrumbs">
        <a href="/" class="kt-subheader__breadcrumbs-home">
          <i class="flaticon2-shelter"></i>
        </a>
        <span class="kt-subheader__breadcrumbs-separator"></span>
        <a
          :href="$route.path"
          class="kt-subheader__breadcrumbs-link"
        >{{ name }}</a>
        <span class="kt-subheader__breadcrumbs-separator"></span>

        <!-- <span class="kt-subheader__breadcrumbs-link kt-subheader__breadcrumbs-link--active">Active link</span> -->
      </div>
    </div>
  </div>

  <!-- end:: Content Head -->
</template>

<script>
export default {
  name: "Breadcrumb",
  data() {
    return {
      name: null
    }
  },
  watch: {
    "$route.params": {
      handler(newValue) {
        this.name = newValue.name
      },
      immediate: true
    }
  }
};
</script>
