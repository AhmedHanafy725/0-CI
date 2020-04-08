<template>
  <div class="kt-grid__item kt-grid__item--fluid kt-grid kt-grid--hor">
    <!-- begin:: Content Head -->
    <content-head></content-head>
    <!-- end:: Content Head -->

    <!-- begin:: Content -->
    <div class="kt-content  kt-grid__item kt-grid__item--fluid" id="kt_content">
      <!--Begin::Dashboard 1-->
      <activity-sec></activity-sec>
      <!--End::Dashboard 1-->
    </div>

    <!-- end:: Content -->
  </div>
</template>

<script>
import ContentHead from "./ContentHead";
import Activity from "./Activity";
export default {
  name: "MainContent",
  components: {
    "content-head": ContentHead,
    "activity-sec": Activity
  }
};
</script>
