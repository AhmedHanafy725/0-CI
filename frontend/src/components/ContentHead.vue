<template>
  <!-- begin:: Content Head -->
  <div class="kt-subheader kt-grid__item" id="kt_subheader">
    <div class="kt-subheader__main">
      <!-- <h3 class="kt-subheader__title">Dashboard</h3> -->
      <span class="kt-subheader__separator kt-hidden"></span>
      <!-- <v-breadcrumbs></v-breadcrumbs> -->
    </div>
  </div>

  <!-- end:: Content Head -->
</template>

<script>
import Breadcrumb from "./Breadcrumb";
export default {
  name: "contentHead",
  components: {
    "v-breadcrumbs": Breadcrumb
  }
};
</script>
