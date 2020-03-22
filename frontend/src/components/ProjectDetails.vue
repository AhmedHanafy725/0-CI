<template>
  <!-- begin:: Content -->
  <div class="kt-content kt-grid__item kt-grid__item--fluid" id="kt_content">
    <div class="kt-portlet kt-portlet--mobile">
      <div class="kt-portlet__head kt-portlet__head--lg">
        <div class="kt-portlet__head-label">
          <span class="kt-portlet__head-icon">
            <i class="kt-font-brand flaticon2-line-chart"></i>
          </span>
          <h3 class="kt-portlet__head-title">{{ name }}</h3>
        </div>
        <div class="kt-header__topbar pr-0">
          <button type="button" class="btn btn-primary btn-sm" @click="restart()">
            <i class="flaticon2-reload"></i> Restart build
          </button>
          <button
            type="button"
            class="kt-demo-icon mb-0"
            data-toggle="modal"
            data-target="#kt_modal_4"
            @click="runConfig()"
          >
            <i class="flaticon2-settings"></i>
          </button>
        </div>
      </div>
      <div class="kt-portlet__body">
        <v-card>
          <v-card-title>
            <!-- title -->
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>

            <v-text-field v-model="search" append-icon="mdi-magnify" label="Search"></v-text-field>
          </v-card-title>
          <v-data-table :headers="headers" :items="details" :search="search">
            <template v-slot:item.id="{ item }">
              <router-link
                :to="'/projects/' + name + '/' + item.id"
                :class="{'disabled': item.status == 'pending'}"
              >{{details.length - details.map(function(x) {return x.id; }).indexOf(item.id)}}</router-link>
            </template>

            <template v-slot:item.status="{ item }">
              <v-chip :color="getStatus(item.status)" dark>{{ item.status }}</v-chip>
            </template>

            <template v-slot:item.timestamp="{ item }">
              <span>{{ time2TimeAgo(item.timestamp) }}</span>
            </template>
          </v-data-table>
        </v-card>
      </div>
    </div>
    <!--begin::Modal-->
    <div
      class="modal fade"
      id="kt_modal_4"
      tabindex="-1"
      role="dialog"
      aria-labelledby="exampleModalLabel"
      aria-hidden="true"
      v-if="newKeyModel"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="exampleModalLabel">keys</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <!--begin::Form-->
            <form class="kt-form kt-form--label-right">
              <div class="kt-portlet__body">
                <div class="form-group row">
                  <div class="col">
                    <label for="key" class="col-2 col-form-label">Key</label>
                    <input class="col-9 form-control" type="text" required />
                  </div>
                  <div class="col">
                    <label for="value" class="col-2 col-form-label">Value</label>
                    <input class="col-9 form-control" type="text" required />
                  </div>
                </div>
              </div>
              <div class="kt-portlet__foot text-right">
                <div class="kt-form__actions">
                  <div class="row">
                    <div class="col">
                      <button type="submit" class="btn btn-success" @click="addKey()">Add</button>
                      <button type="reset" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!--end::Modal-->
  </div>

  <!-- end:: Content -->
</template>

<script>
import axios from "axios";
export default {
  name: "ProjectDetails",
  props: ["name"],
  data() {
    return {
      search: "",
      headers: [
        { text: "#ID", value: "id" },
        { text: "Status", value: "status" },
        { text: "Time", value: "timestamp" }
      ],
      details: [],
      newKeyModel: true
    };
  },
  methods: {
    clear() {
      this.details = [];
    },
    getDetails() {
      const path = process.env.VUE_APP_BASE_URL + `projects/${this.formatOrg}`;
      axios
        .get(path)
        .then(response => {
          this.details = response.data;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    getStatus(status) {
      if (status == "error") return "kt-bg-error";
      else if (status == "failure") return "kt-bg-failure";
      else if (status == "success") return "kt-bg-success";
      else return "orange";
    },
    time2TimeAgo(ts) {
      var d = new Date();
      var nowTs = Math.floor(d.getTime() / 1000);
      var seconds = nowTs - ts;

      // more that two days
      if (seconds > 2 * 24 * 3600) {
        return "a few days ago";
      }
      // a day
      if (seconds > 24 * 3600) {
        return "yesterday";
      }

      if (seconds > 3600) {
        return "a few hours ago";
      }
      if (seconds > 1800) {
        return "Half an hour ago";
      }
      if (seconds > 60) {
        return Math.floor(seconds / 60) + " minutes ago";
      }
    },
    restart() {
      const path = "https://staging.zeroci.grid.tf/run_trigger/";
      axios
        .post(
          path,
          { id: "4" },
          {
            headers: {
              "Content-Type": "application/json",
              "Access-Control-Allow-Origin": "*"
            }
          }
        )
        .then(response => {
          console.log(response);
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    runConfig() {
      const path = `https://staging.zeroci.grid.tf/api/run_config/${this.name}`;
      axios
        .get(path)
        .then(response => {
          if (Object.keys(response.data).length === 0) {
            this.newKeyModel = true;
          } else {
            console.log(response.data);
          }
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    addKey() {
      const path = `https://staging.zeroci.grid.tf/api/run_config/`;
      axios
        .post(
          path,
          { key: this.key, value: this.value },
          {
            headers: {
              "Content-Type": "application/json",
              "Access-Control-Allow-Origin": "*"
            }
          }
        )
        .then(response => {
          console.log(response);
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    }
  },
  computed: {
    formatOrg() {
      return this.name.split(" ").join("%20");
    }
  },
  created() {
    this.getDetails();
  },
  watch: {
    "$route.params": {
      handler(newValue) {
        this.clear();
        const { name } = newValue;
        this.getDetails();
      },
      immediate: true
    }
  }
};
</script>
