<template>
  <v-breadcrumbs :items="breadcrumbs" divider=">">
    <v-breadcrumbs-item slot="item" slot-scope="{ item }" exact :to="item.to">{{ item.text }}</v-breadcrumbs-item>
  </v-breadcrumbs>
</template>

<script>
export default {
  name: "Breadcrumb",

};
</script>
