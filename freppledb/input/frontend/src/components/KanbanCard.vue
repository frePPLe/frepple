/* * Copyright (C) 2025 by frePPLe bv * * Permission is hereby granted, free of charge, to any
person obtaining * a copy of this software and associated documentation files (the * "Software"), to
deal in the Software without restriction, including * without limitation the rights to use, copy,
modify, merge, publish, * distribute, sublicense, and/or sell copies of the Software, and to *
permit persons to whom the Software is furnished to do so, subject to * the following conditions: *
* The above copyright notice and this permission notice shall be * included in all copies or
substantial portions of the Software. * * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF * MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION * OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION * WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE */

<script setup lang="js">
import { computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@/stores/operationplansStore.js';
import {numberFormat, dateTimeFormat, adminEscape, dateFormat} from '@common/utils.js';

onMounted(() => {
  const target = document.getElementById('kanban');
});

const urlPrefix = computed(() => window.urlPrefix || '');

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true,
});

const store = useOperationplansStore();

const props = defineProps({
  opplan: {
    type: Object,
    default: () => {}
  },
  opplan_index: {
    type: Number,
    default: 0
  }
});

const mode = window.mode;
const editable = true;
const calendarmode = "duration";

function isStart(opplan, dt) {
  const d = opplan.startdate || opplan.operationplan__startdate;
  if (!d)
    return false;
  else if (dt instanceof Date)
    return d.getFullYear() === dt.getFullYear() && d.getMonth() === dt.getMonth() && d.getDate() === dt.getDate();
  else
    return window.moment(d).isSame(dt.date, "day");
}

function isEnd(opplan, dt) {
  let d = opplan.enddate || opplan.operationplan__enddate;
  if (!d)
    return false;
  // Subtract 1 microsecond to assure that an end date of 00:00:00 is seen
  // as ending on the previous day.
  if (d > (opplan.startdate || opplan.operationplan__startdate))
    d = new Date(d - 1);
  if (dt instanceof Date)
    return d.getFullYear() === dt.getFullYear() && d.getMonth() === dt.getMonth() && d.getDate() === dt.getDate();
  else
    return window.moment(d).isSame(dt.date, "day");
}

</script>

<template>
  <div
    :draggable="editable ? 'true' : 'false'"
    class="card"
    :class="
      (mode === 'calendarweek' || mode === 'calendarday') && calendarmode === 'duration'
        ? 'calendar-event-inner'
        : '' + ',' + opplan.hasOwnProperty('selected')
          ? 'active'
          : '' + ',' + opplan.dirty
            ? 'dirty'
            : ''
    "
    :style="{ 'overflow-y': 'hidden', 'background-color': opplan.color }"
    :data-index="props.opplan_index"
    :data-reference="opplan.id || opplan.reference"
  >
    <div>{{opplan["type"]}} CARD</div>
    <div v-if="opplan.type === 'PO'">
      <p>
        <span v-if="opplan.dirty && !opplan.selected" class="badge bg-danger float-end">
          ttt('unsaved')
        </span>
<!--        this is for dragging-->
<!--        <i v-if="isStart(opplan, dt)" class="fa fa-step-backward"></i>&nbsp;-->
        <i
          class="fa fa-shopping-cart"
          data-bs-toggle="tooltip"
          data-bs-html="true"
          :title="ttt('Purchase Order')"
        ></i>&nbsp;
        <strong>{{ opplan.operationplan__reference || opplan.reference }}</strong>&nbsp;
        <!--        this is for dragging-->
<!--        <i v-if="isEnd(opplan, dt)" class="fa fa-step-forward"></i>&nbsp;-->
        <i
          v-if="!editable || !opplan.hasOwnProperty('selected')"
          class="fa"
          :class="(opplan.status === 'confirmed' || opplan.operationplan__status === 'confirmed')?'fa-lock':'' + ',' + (opplan.status ==='approved' || opplan.operationplan__status ==='approved')?'fa-unlock-alt': '' + ',' + (opplan.status ==='proposed' || opplan.operationplan__status ==='proposed')?'fa-unlock': '' + ',' + (opplan.status ==='completed' || opplan.operationplan__status ==='completed')?'fa-check': '' + ',' + (opplan.status ==='closed' || opplan.operationplan__status ==='closed')?'fa-times': ''"
          aria-hidden="true"
        ></i>
        <span class="btn-group" role="group" v-if="editable && opplan.hasOwnProperty('selected')">
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status === 'proposed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('proposed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'proposed');
              opplan.status = 'proposed';
            "
          >
            <i class="fa fa-unlock"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status === 'approved' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('approved')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'approved');
              opplan.status = 'approved';
            "
          >
            <i class="fa fa-unlock-alt"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status === 'confirmed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('confirmed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'confirmed');
              opplan.status = 'confirmed';
            "
          >
            <i class="fa fa-lock"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status === 'completed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('completed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'completed');
              opplan.status = 'completed';
            "
          >
            <i class="fa fa-check"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status === 'closed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('closed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'closed');
              opplan.status = 'closed';
            "
          >
            <i class="fa fa-times"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='proposed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('proposed')"
            @click="
              changeCard(opplan, 'operationplan__status', opplan.operationplan__status, 'proposed');
              opplan.operationplan__status = 'proposed';
            "
          >
            <i class="fa fa-unlock"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='approved' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('approved')"
            @click="
              changeCard(opplan, 'operationplan__status', opplan.operationplan__status, 'approved');
              opplan.operationplan__status = 'approved';
            "
          >
            <i class="fa fa-unlock-alt"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='confirmed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('confirmed')"
            @click="
              changeCard(
                opplan,
                'operationplan__status',
                opplan.operationplan__status,
                'confirmed'
              );
              opplan.operationplan__status = 'confirmed';
            "
          >
            <i class="fa fa-lock"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='completed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('completed')"
            @click="
              changeCard(
                opplan,
                'operationplan__status',
                opplan.operationplan__status,
                'completed'
              );
              opplan.operationplan__status = 'completed';
            "
          >
            <i class="fa fa-check"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='closed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('closed')"
            @click="
              changeCard(opplan, 'operationplan__status', opplan.operationplan__status, 'closed');
              opplan.operationplan__status = 'closed';
            "
          >
            <i class="fa fa-times"></i>
          </button>
        </span>
      </p>
      <p>
        {{ opplan.item__name || opplan.item }}&nbsp;
        <a
          @click.stop=""
          :href="
            urlPrefix +
            '/detail/input/item/' +
            adminEscape(opplan.item__name || opplan.item) +
            '/'
          "
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p v-if="opplan.item__description || opplan.operationplan__item__description">
        {{ opplan.item__description || opplan.operationplan__item__description }}&nbsp;
      </p>
      <p>
        {{ opplan.location }}&nbsp;
        <a
          @click.stop=""
          :href="urlPrefix + '/detail/input/location/' + adminEscape(opplan.location) + '/'"
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p>
        {{ opplan.operationplan__supplier || opplan.supplier }}&nbsp;
        <a
          @click.stop=""
          :href="urlPrefix + '/detail/input/supplier/' + adminEscape(opplan.supplier) + '/'"
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p
        :class="(opplan.hasOwnProperty('quantityOriginal') || opplan.hasOwnProperty('operationplan__quantityOriginal'))?'dirty': ''"
      >
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          numberFormat(opplan.operationplan__quantity || opplan.quantity)
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__quantity')
          "
          type="number"
          step="0"
          min="0"
          @focus="oldValue = opplan.quantity"
          v-model="opplan.quantity"
          @change="changeCard(opplan, 'quantity', oldValue, opplan.quantity)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__quantity')
          "
          type="number"
          step="0"
          min="0"
          @focus="oldValue = opplan.operationplan__quantity"
          v-model="opplan.operationplan__quantity"
          @change="
            changeCard(opplan, 'operationplan__quantity', oldValue, opplan.operationplan__quantity)
          "
        />
      </p>
      <p
        :class="
          opplan.hasOwnProperty('startdateOriginal') ||
          opplan.hasOwnProperty('operationplan__startdateOriginal')
            ? 'dirty'
            : ''
        "
      >
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          dateFormat(opplan.operationplan__startdate || opplan.startdate)
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__startdate')
          "
          type="date"
          @focus="oldValue = opplan.startdate"
          v-model="opplan.startdate"
          @change="changeCard(opplan, 'startdate', oldValue, opplan.startdate)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__startdate')
          "
          type="date"
          @focus="oldValue = opplan.operationplan__startdate"
          v-model="opplan.operationplan__startdate"
          @change="
            changeCard(
              opplan,
              'operationplan__startdate',
              oldValue,
              opplan.operationplan__startdate
            )
          "
        />
      </p>
      <p
        :class="
          opplan.hasOwnProperty('enddateOriginal') ||
          opplan.hasOwnProperty('operationplan__enddateOriginal')
            ? 'dirty'
            : ''
        "
      >
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          dateFormat(opplan.operationplan__enddate || opplan.enddate)
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__enddate')
          "
          type="date"
          @focus="oldValue = opplan.enddate"
          v-model="opplan.enddate"
          @change="changeCard(opplan, 'enddate', oldValue, opplan.enddate)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__enddate')
          "
          type="date"
          @focus="oldValue = opplan.operationplan__enddate"
          v-model="opplan.operationplan__enddate"
          @change="
            changeCard(opplan, 'operationplan__enddate', oldValue, opplan.operationplan__enddate)
          "
        />
      </p>
      <p v-if="opplan.remark || opplan.operationplan__remark">
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          opplan.remark || opplan.operationplan__remark
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__remark')
          "
          @focus="oldValue = opplan.remark"
          v-model="opplan.remark"
          @change="changeCard(opplan, 'remark', oldValue, opplan.remark)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__remark')
          "
          @focus="oldValue = opplan.operationplan__remark"
          v-model="opplan.operationplan__remark"
          @change="
            changeCard(opplan, 'operationplan__remark', oldValue, opplan.operationplan__remark)
          "
        />
      </p>
    </div>
    <div v-if="(opplan.type || opplan.operationplan__type || type) === 'DO'">
      <p>
        <span v-if="opplan.dirty && !opplan.selected" class="badge bg-danger float-end">{{
          ttt('unsaved')
        }}</span>
        <!--        this is for dragging-->
<!--        <i v-if="isStart(opplan, dt)" class="fa fa-step-backward"></i>&nbsp;-->
        <i
          class="fa fa-truck"
          data-bs-toggle="tooltip"
          data-bs-html="true"
          :title="ttt('Distribution Order')"
        ></i
        >&nbsp; <strong>{{ opplan.operationplan__reference || opplan.reference }}</strong>&nbsp;
        <!--        this is for dragging-->
<!--        <i v-if="isEnd(opplan, dt)" class="fa fa-step-forward"></i>&nbsp;-->
        <i
          v-if="!editable || !opplan.hasOwnProperty('selected')"
          class="fa"
          :class="
            opplan.status ==='confirmed' || opplan.operationplan__status ==='confirmed'
              ? 'fa-lock'
              : '' +
                  ',' +
                  (opplan.status ==='approved' || opplan.operationplan__status ==='approved')
                ? 'fa-unlock-alt'
                : '' +
                    ',' +
                    (opplan.status ==='proposed' || opplan.operationplan__status ==='proposed')
                  ? 'fa-unlock'
                  : '' +
                      ',' +
                      (opplan.status ==='completed' || opplan.operationplan__status ==='completed')
                    ? 'fa-check'
                    : '' +
                        ',' +
                        (opplan.status ==='closed' || opplan.operationplan__status ==='closed')
                      ? 'fa-times'
                      : ''
          "
          aria-hidden="true"
        ></i>
        <span class="btn-group" role="group" v-if="editable && opplan.hasOwnProperty('selected')">
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status ==='proposed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('proposed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'proposed');
              opplan.status = 'proposed';
            "
          >
            <i class="fa fa-unlock"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status ==='approved' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('approved')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'approved');
              opplan.status = 'approved';
            "
          >
            <i class="fa fa-unlock-alt"></i>
          </button>
          <!--          the next 3 buttons from angular check for operationplan__status but use opplan.status-->
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status ==='confirmed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('confirmed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'confirmed');
              opplan.status = 'confirmed';
            "
          >
            <i class="fa fa-lock"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status ==='completed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('completed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'completed');
              opplan.status = 'completed';
            "
          >
            <i class="fa fa-check"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status ==='closed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('closed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'closed');
              opplan.status = 'closed';
            "
          >
            <i class="fa fa-times"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='proposed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('proposed')"
            @click="
              changeCard(opplan, 'operationplan__status', opplan.operationplan__status, 'proposed');
              opplan.operationplan__status = 'proposed';
            "
          >
            <i class="fa fa-unlock"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='approved' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('approved')"
            @click="
              changeCard(opplan, 'operationplan__status', opplan.operationplan__status, 'approved');
              opplan.operationplan__status = 'approved';
            "
          >
            <i class="fa fa-unlock-alt"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='confirmed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('confirmed')"
            @click="
              changeCard(
                opplan,
                'operationplan__status',
                opplan.operationplan__status,
                'confirmed'
              );
              opplan.operationplan__status = 'confirmed';
            "
          >
            <i class="fa fa-lock"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='completed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('completed')"
            @click="
              changeCard(
                opplan,
                'operationplan__status',
                opplan.operationplan__status,
                'completed'
              );
              opplan.operationplan__status = 'completed';
            "
          >
            <i class="fa fa-check"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='closed' ? 'active' : ''"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('closed')"
            @click="
              changeCard(opplan, 'operationplan__status', opplan.operationplan__status, 'closed');
              opplan.operationplan__status = 'closed';
            "
          >
            <i class="fa fa-times"></i>
          </button>
        </span>
      </p>
      <p>
        {{ opplan.item__name || opplan.item }}&nbsp;
        <a
          @click.stop=""
          :href="
            urlPrefix +
            '/detail/input/item/' +
            adminEscape(opplan.item__name || opplan.item) +
            '/'
          "
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p v-if="opplan.item__description || opplan.operationplan__item__description">
        {{ opplan.item__description || opplan.operationplan__item__description }}&nbsp;
      </p>
      <p>
        {{ opplan.operationplan__origin || opplan.origin }}&nbsp;
        <a
          @click.stop=""
          :href="
            urlPrefix +
            '/detail/input/location/' +
            adminEscape(opplan.operationplan__origin || opplan.origin) +
            '/'
          "
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p>
        {{
          opplan.destination ||
          opplan.operationplan__destination ||
          opplan.operationplan__location ||
          opplan.location
        }}&nbsp;
        <a
          @click.stop=""
          :href="
            urlPrefix +
            '/detail/input/location/' +
            adminEscape(
              opplan.destination ||
                opplan.operationplan__destination ||
                opplan.operationplan__location ||
                opplan.location
            ) +
            '/'
          "
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p
        :class="
          opplan.hasOwnProperty('quantityOriginal') ||
          opplan.hasOwnProperty('operationplan__quantityOriginal')
            ? 'dirty'
            : ''
        "
      >
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          numberFormat(opplan.operationplan__quantity || opplan.quantity)
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__quantity')
          "
          type="number"
          step="0"
          min="0"
          @focus="oldValue = opplan.quantity"
          v-model="opplan.quantity"
          @change="changeCard(opplan, 'quantity', oldValue, opplan.quantity)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__quantity')
          "
          type="number"
          step="0"
          min="0"
          @focus="oldValue = opplan.operationplan__quantity"
          v-model="opplan.operationplan__quantity"
          @change="
            changeCard(opplan, 'operationplan__quantity', oldValue, opplan.operationplan__quantity)
          "
        />
      </p>
      <p
        :class="
          opplan.hasOwnProperty('startdateOriginal') ||
          opplan.hasOwnProperty('operationplan__startdateOriginal')
            ? 'dirty'
            : ''
        "
      >
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          dateFormat(opplan.operationplan__startdate || opplan.startdate)
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__startdate')
          "
          type="date"
          @focus="oldValue = opplan.startdate"
          v-model="opplan.startdate"
          @change="changeCard(opplan, 'startdate', oldValue, opplan.startdate)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__startdate')
          "
          type="date"
          @focus="oldValue = opplan.operationplan__startdate"
          v-model="opplan.operationplan__startdate"
          @change="
            changeCard(
              opplan,
              'operationplan__startdate',
              oldValue,
              opplan.operationplan__startdate
            )
          "
        />
      </p>
      <p
        :class="
          opplan.hasOwnProperty('enddateOriginal') ||
          opplan.hasOwnProperty('operationplan__enddateOriginal')
            ? 'dirty'
            : ''
        "
      >
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          dateTimeFormat(opplan.operationplan__enddate || opplan.enddate)
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__enddate')
          "
          type="date"
          @focus="oldValue = opplan.enddate"
          v-model="opplan.enddate"
          @change="changeCard(opplan, 'enddate', oldValue, opplan.enddate)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__enddate')
          "
          type="date"
          @focus="oldValue = opplan.operationplan__enddate"
          v-model="opplan.operationplan__enddate"
          @change="
            changeCard(opplan, 'operationplan__enddate', oldValue, opplan.operationplan__enddate)
          "
        />
      </p>
      <p v-if="opplan.remark || opplan.operationplan__remark">
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          opplan.remark || opplan.operationplan__remark
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__remark')
          "
          @focus="oldValue = opplan.remark"
          v-model="opplan.remark"
          @change="changeCard(opplan, 'remark', oldValue, opplan.remark)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__remark')
          "
          @focus="oldValue = opplan.operationplan__remark"
          v-model="opplan.operationplan__remark"
          @change="
            changeCard(opplan, 'operationplan__remark', oldValue, opplan.operationplan__remark)
          "
        />
      </p>
    </div>
    <div v-if="opplan.type === 'MO' || opplan.type === 'WO'">
      <p>
        <span v-if="opplan.dirty && !opplan.selected" class="badge bg-danger float-end">{{
          ttt('unsaved')
        }}</span>
        <!--        this is for dragging-->
<!--        <i v-if="isStart(opplan, dt)" class="fa fa-step-backward"></i>&nbsp;-->
        <i
          class="fa fa-wrench"
          data-bs-toggle="tooltip"
          data-bs-html="true"
          :title="ttt('Manufacturing Order')"
        ></i>&nbsp;
        <strong>{{ opplan.operationplan__reference || opplan.reference }}</strong>
        &nbsp;
        <!--        this is for dragging-->
<!--        <i v-if="isEnd(opplan, dt)" class="fa fa-step-forward"></i>&nbsp;-->
        <i
          v-if="!editable || !opplan.hasOwnProperty('selected')"
          class="fa"
          :class="
            opplan.status ==='confirmed' || opplan.operationplan__status ==='confirmed'
              ? 'fa-lock'
              : '' +
                  ',' +
                  (opplan.status ==='approved' || opplan.operationplan__status ==='approved')
                ? 'fa-unlock-alt'
                : '' +
                    ',' +
                    (opplan.status ==='proposed' || opplan.operationplan__status ==='proposed')
                  ? 'fa-unlock'
                  : '' +
                      ',' +
                      (opplan.status ==='completed' || opplan.operationplan__status ==='completed')
                    ? 'fa-check'
                    : '' +
                        ',' +
                        (opplan.status ==='closed' || opplan.operationplan__status ==='closed')
                      ? 'fa-times'
                      : ''
          "
          aria-hidden="true"
        ></i>
        <span class="btn-group" role="group" v-if="editable && opplan.hasOwnProperty('selected')">
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status ==='proposed'"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('proposed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'proposed');
              opplan.status = 'proposed';
            "
          >
            <i class="fa fa-unlock"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status ==='approved'"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('approved')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'approved');
              opplan.status = 'approved';
            "
          >
            <i class="fa fa-unlock-alt"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status ==='confirmed'"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('confirmed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'confirmed');
              opplan.status = 'confirmed';
            "
          >
            <i class="fa fa-lock"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status ==='completed'"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('completed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'completed');
              opplan.status = 'completed';
            "
          >
            <i class="fa fa-check"></i>
          </button>
          <button
            v-if="!opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.status ==='closed'"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('closed')"
            @click="
              changeCard(opplan, 'status', opplan.status, 'closed');
              opplan.status = 'closed';
            "
          >
            <i class="fa fa-times"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='proposed'"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('proposed')"
            @click="
              changeCard(opplan, 'operationplan__status', opplan.operationplan__status, 'proposed');
              opplan.operationplan__status = 'proposed';
            "
          >
            <i class="fa fa-unlock"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='approved'"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('approved')"
            @click="
              changeCard(opplan, 'operationplan__status', opplan.operationplan__status, 'approved');
              opplan.operationplan__status = 'approved';
            "
          >
            <i class="fa fa-unlock-alt"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='confirmed'"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('confirmed')"
            @click="
              changeCard(
                opplan,
                'operationplan__status',
                opplan.operationplan__status,
                'confirmed'
              );
              opplan.operationplan__status = 'confirmed';
            "
          >
            <i class="fa fa-lock"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='completed'"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('completed')"
            @click="
              changeCard(
                opplan,
                'operationplan__status',
                opplan.operationplan__status,
                'completed'
              );
              opplan.operationplan__status = 'completed';
            "
          >
            <i class="fa fa-check"></i>
          </button>
          <button
            v-if="opplan.hasOwnProperty('operationplan__status')"
            type="button"
            class="btn, btn-sm, btn-primary"
            :class="opplan.operationplan__status ==='closed'"
            data-bs-toggle="tooltip"
            data-bs-html="true"
            :title="ttt('closed')"
            @click="
              changeCard(opplan, 'operationplan__status', opplan.operationplan__status, 'closed');
              opplan.operationplan__status = 'closed';
            "
          >
            <i class="fa fa-times"></i>
          </button>
        </span>
      </p>
      <p v-if="opplan.item__name || opplan.operationplan__item__name">
        {{ opplan.item__name || opplan.operationplan__item__name }}&nbsp;
        <a
          @click.stop=""
          :href="urlPrefix + '/detail/input/item/' + adminEscape(opplan.item__name || opplan.operationplan__item__name) + '/'"
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p v-if="opplan.item__description || opplan.operationplan__item__description">
        {{ opplan.item__description || opplan.operationplan__item__description }}&nbsp;
      </p>
      <p>
<!--        this <P> has changes compared to angular -->
        {{
          opplan.operationplan__name || opplan.operationplan__operation__name || opplan.operation.name
        }}&nbsp;
        <a
          @click.stop=""
          :href="urlPrefix + '/detail/input/operation/' + adminEscape(opplan.operationplan__name || opplan.operationplan__operation__name || opplan.operation.name) + '/'"
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p v-if="opplan.operation__description || opplan.operationplan__operation__description">
        {{ opplan.operation__description || opplan.operationplan__operation__description }}&nbsp;
      </p>
      <p
        data-ng-class="{'dirty': opplan.hasOwnProperty('quantityOriginal') || opplan.hasOwnProperty('operationplan__quantityOriginal')}"
      >
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          numberFormat(opplan.operationplan__quantity || opplan.quantity)
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__quantity')
          "
          type="number"
          step="0"
          min="0"
          @focus="oldValue = opplan.operationplan__quantity"
          v-model="opplan.operationplan__quantity"
          @change="
            changeCard(opplan, 'operationplan__quantity', oldValue, opplan.operationplan__quantity)
          "
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__quantity')
          "
          type="number"
          step="0"
          min="0"
          @focus="oldValue = opplan.quantity"
          v-model="opplan.quantity"
          @change="changeCard(opplan, 'quantity', oldValue, opplan.quantity)"
        />
      </p>
      <p
        :class="(opplan.hasOwnProperty('quantity_completedOriginal') || opplan.hasOwnProperty('operationplan__quantity_completedOriginal'))?'dirty':''"
      >
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          numberFormat(
            opplan.operationplan__quantity_completed || opplan.quantity_completed || 0
          )
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__quantity')
          "
          type="number"
          step="0"
          min="0"
          @focus="oldValue = opplan.operationplan__quantity_completed || 0"
          v-model="opplan.operationplan__quantity_completed"
          @change="
            changeCard(
              opplan,
              'operationplan__quantity_completed',
              oldValue,
              opplan.operationplan__quantity_completed
            )
          "
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__quantity')
          "
          type="number"
          step="0"
          min="0"
          @focus="oldValue = opplan.quantity_completed || 0"
          v-model="opplan.quantity_completed"
          @change="changeCard(opplan, 'quantity_completed', oldValue, opplan.quantity_completed)"
        />
      </p>
      <p
        :class="(opplan.hasOwnProperty('startdateOriginal') || opplan.hasOwnProperty('operationplan__startdateOriginal'))?'dirty':''"
      >
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          dateFormat(opplan.operationplan__startdate || opplan.startdate)
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__startdate')
          "
          type="datetime-local"
          @focus="oldValue = opplan.startdate"
          v-model="opplan.startdate"
          @change="changeCard(opplan, 'startdate', oldValue, opplan.startdate)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__startdate')
          "
          type="datetime-local"
          @focus="oldValue = opplan.operationplan__startdate"
          v-model="opplan.operationplan__startdate"
          @change="
            changeCard(
              opplan,
              'operationplan__startdate',
              oldValue,
              opplan.operationplan__startdate
            )
          "
        />
      </p>
      <p
        :class="(opplan.hasOwnProperty('enddateOriginal') || opplan.hasOwnProperty('operationplan__enddateOriginal'))?'dirty':''"
      >
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          dateFormat(opplan.operationplan__enddate || opplan.enddate)
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__enddate')
          "
          type="datetime-local"
          @focus="oldValue = opplan.enddate"
          v-model="opplan.enddate"
          @change="changeCard(opplan, 'enddate', oldValue, opplan.enddate)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__enddate')
          "
          type="datetime-local"
          @focus="oldValue = opplan.operationplan__enddate"
          v-model="opplan.operationplan__enddate"
          @change="
            changeCard(opplan, 'operationplan__enddate', oldValue, opplan.operationplan__enddate)
          "
        />
      </p>
      <p v-if="opplan.remark || opplan.operationplan__remark">
        <span v-if="!editable || !opplan.hasOwnProperty('selected')">{{
          opplan.remark || opplan.operationplan__remark
        }}</span>
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            !opplan.hasOwnProperty('operationplan__remark')
          "
          @focus="oldValue = opplan.remark"
          v-model="opplan.remark"
          @change="changeCard(opplan, 'remark', oldValue, opplan.remark)"
        />
        <input
          class="form-control"
          v-if="
            editable &&
            opplan.hasOwnProperty('selected') &&
            opplan.hasOwnProperty('operationplan__remark')
          "
          @focus="oldValue = opplan.operationplan__remark"
          v-model="opplan.operationplan__remark"
          @change="
            changeCard(opplan, 'operationplan__remark', oldValue, opplan.operationplan__remark)
          "
        />
      </p>
    </div>
    <div data-no-drag v-if="opplan.type === 'STCK'">
      <p>
        <i
          class="fa fa-box"
          data-bs-toggle="tooltip"
          data-bs-html="true"
          :title="ttt('Stock')"
        ></i
        >&nbsp; <strong>{{ opplan.item__name }} @ {{ opplan.location }}</strong
        >&nbsp;
        <a
          @click.stop=""
          :href="urlPrefix + '/detail/input/buffer/' + adminEscape(opplan.item__name + ' @ ' + opplan.location ) + '/'"
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p v-if="opplan.item__description || opplan.operationplan__item__description">
        {{ opplan.item__description || opplan.operationplan__item__description }}&nbsp;
      </p>
      <p>{{ numberFormat(opplan.operationplan__quantity || opplan.quantity) }}</p>
    </div>
    <div data-no-drag v-if="opplan.type === 'DLVR'">
      <p>
        <i
          class="fa fa-truck"
          data-bs-toggle="tooltip"
          data-bs-html="true"
          :title="ttt('Delivery')"
        ></i
        >&nbsp;
        <strong>{{ opplan.demands[0][1] }}</strong>
      </p>
      <p v-if="opplan.item__name">
        {{ opplan.item }}&nbsp;
        <a
          @click.stop=""
          :href="urlPrefix + '/detail/input/item/' + adminEscape(opplan.item__name) + '/'"
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p v-if="opplan.item__description || opplan.operationplan__item__description">
        {{ opplan.item__description || opplan.operationplan__item__description }}&nbsp;
      </p>
      <p>
        {{ opplan.location }}&nbsp;
        <a
          @click.stop=""
          :href="urlPrefix + '/detail/input/location/' + adminEscape(opplan.location) + '/'"
        >
          <i class="fa fa-caret-right"></i>
        </a>
      </p>
      <p>{{ dateFormat(opplan.operationplan__enddate || opplan.enddate) }}</p>
      <p>{{ numberFormat(opplan.operationplan__quantity || opplan.quantity) }}</p>
    </div>
  </div>
</template>
